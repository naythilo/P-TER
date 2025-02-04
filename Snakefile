import os
import pandas
import tempfile
import json
import gdown
import signal
import pandas
import tempfile
import requests
import threading
import subprocess
import SPARQLWrapper
import re

# Définition des ports des serveurs
VIRTUOSO_PORT = 8890
FUSEKI_PORT = 3030

JENA_HOME = f"{os.getcwd()}/apache-jena-4.9.0"
FUSEKI_HOME = f"{os.getcwd()}/apache-jena-fuseki-4.9.0"
VIRTUOSO_HOME = f"{os.getcwd()}/virtuoso-opensource-7.2.7"

# Timeout pour chaque requête
TIMEOUT = 1200  # 20 minutes

# Nombre d'exécutions par requête
RUNS = [1, 2, 3]

# Liste des workloads
WORKLOADS = ["rdfs"]
APPROACHES = ["fuseki", "virtuoso"]
QUERIES = ["q05"]

# VARS DE CONFIG DU SNAKEFILE
DO_INSTALL = True
KEEP_ALIVE = False

# Fonction pour récupérer les requêtes SPARQL
def get_queries(workload):
    query_dir = f"queries/{workload}"
    return [os.path.splitext(q)[0] for q in os.listdir(query_dir) if q.endswith(".sparql")]

if DO_INSTALL:

    rule install_apache_jena_fuseki:
        priority: 100
        output: directory(FUSEKI_HOME)
        shell:
            """
            echo "Downloading Apache Jena Fuseki..."
            wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.9.0.tar.gz
            echo "Extracting Apache Jena Fuseki..."
            tar -zxf apache-jena-fuseki-4.9.0.tar.gz -C {FUSEKI_HOME}
            """

    rule install_apache_jena:
        priority: 100
        output:
            jena = directory(JENA_HOME),
            jena_loader = f"{JENA_HOME}/bin/tdb2.xloader"
        shell:
            f"""
            wget https://archive.apache.org/dist/jena/binaries/apache-jena-4.9.0.tar.gz
            tar -zxf apache-jena-4.9.0.tar.gz -C {JENA_HOME}
            """

    rule install_virtuoso:
        priority: 100
        output:
            virtuoso = directory(VIRTUOSO_HOME),
            virtuoso_isql = f"{VIRTUOSO_HOME}/bin/isql",
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/virtuoso.ini"
        shell:
            f"""
            wget https://github.com/openlink/virtuoso-opensource/releases/download/v7.2.7/virtuoso-opensource-7.2.7.tar.gz
            tar -zxf virtuoso-opensource-7.2.7.tar.gz
            cd virtuoso-opensource-7.2.7
            ./autogen.sh
            ./configure
            make && make install prefix={VIRTUOSO_HOME} && make clean && make distclean
            """

    rule download_datasets:
        output: "datasets/fedshop-virtuoso.db"
        shell:
            """
            gdown https://zenodo.org/records/12204740/files/fedshop-virtuoso.db?download=1 -O datasets/fedshop-virtuoso.db
            """

    rule load_FedShop_into_Virtuoso:
        priority: 100
        input:
            dataset = "datasets/fedshop-virtuoso.db",
            virtuoso = VIRTUOSO_HOME,
            virtuoso_isql = f"{VIRTUOSO_HOME}/bin/isql",
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini"
        output:
            graphs = "config/rdfs/graphs.txt"
        shell:
            """
            python commons.py start-virtuoso --home {input.virtuoso} --config {input.virtuoso_configfile}
            {input.virtuoso_isql} "EXEC=ld_dir('`pwd`/datasets', 'fedshop-virtuoso.db', 'NULL');"
            {input.virtuoso_isql} "EXEC=rdf_loader_run();"
            {input.virtuoso_isql} "EXEC=checkpoint;"
            {input.virtuoso_isql} "EXEC=SPARQL SELECT DISTINCT ?g WHERE {{ GRAPH ?g {{ ?s a ?c }} }};" | egrep "(ratingsite|vendor)[0-9]*" > {output.graphs}
            """

    rule setup_virtuoso:
        priority: 100
        input:
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/virtuoso.ini"
        output:
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini"
        shell:
            f"""
            cp {input.virtuoso_configfile} {output.virtuoso_configfile}
            sed -i -E 's@(^ServerPort.*?= [^(1111)].*?$)@ServerPort = {VIRTUOSO_PORT}@g' {output.virtuoso_configfile}
            sed -i -E 's@(^DefaultHost.*$)@DefaultHost = localhost:{VIRTUOSO_PORT}@g' {output.virtuoso_configfile}
            sed -i -E 's@DirsAllowed(.*)$@DirsAllowed\\1, {os.getcwd()}@g' {output.virtuoso_configfile}
            sed -i -E 's@(^ResultSetMaxRows.*$)@;\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^MaxQueryCostEstimationTime.*$)@;\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^MaxQueryExecutionTime.*$)@;\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^NumberOfBuffers.*$)@;\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^MaxDirtyBuffers.*$)@;\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@^;(NumberOfBuffers.*?= 2720000.*$)@\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@^;(MaxDirtyBuffers.*?= 2000000.*$)@\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^MaxQueryMem.*)@MaxQueryMem = 8G@g' {output.virtuoso_configfile}
            """

    rule generate_endpoints:
        input:
            graphs = "config/{workload}/graphs.txt"
        output:
            endpoints = "config/{workload}/endpoints.txt"
        shell:
            f"sed -E 's@(^.*$)@http://localhost:{VIRTUOSO_PORT}/sparql?default-graph-uri=\\1@g' {input.graphs} > {output.endpoints}"


    rule generate_FedX_configuration_file:
        priority: 100
        input:
            configfile = "config/{approach}.props",
        output:
            configfile = "config/{workload}/{approach}.props"
        shell:
            "cp {input.configfile} {output.configfile}"

rule run_RSA_query:
    priority: 50
    input:
        virtuoso = VIRTUOSO_HOME,
        virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini",
        fuseki = FUSEKI_HOME,
        query = "queries/{workload}-RSA/{query}.sparql",
        endpoints = "config/{workload}/endpoints.txt"
    output:
        metrics = "output/{workload}/{approach}/{query}.{run}.csv",
        solutions = "output/{workload}/{approach}/{query}.{run}.json"
    params:
        timeout = TIMEOUT
    run:
        query_file = tempfile.NamedTemporaryFile()
        shell(f"sed -E 's@http://localhost:[0-9]+/sparql@http://localhost:{VIRTUOSO_PORT}/sparql@g' {input.query} > {query_file.name}")
        shell(f"python commons.py start-virtuoso --home {input.virtuoso} --config {input.virtuoso_configfile} --restart")
        shell(f"python commons.py start-fuseki --home {input.fuseki} --port {FUSEKI_PORT} --restart")
        shell(f"timeout {params.timeout} python commons.py run-rsa-query {query_file.name} --metrics-output {output.metrics} --solutions-output {output.solutions}")
        df = pandas.read_csv(str(output.metrics))
        df["query"] = wildcards.query
        df["workload"] = wildcards.workload
        df["approach"] = wildcards.approach
        df["run"] = wildcards.run
        df.to_csv(str(output.metrics))
        query_file.close()

rule run_all_queries:
    input:
        expand("output/{workload}/{approach}/{query}.{run}.csv", workload=WORKLOADS, approach=APPROACHES, query=QUERIES, run=RUNS)
    output: 
        "output/data.csv"
    run:
        data = [pandas.read_csv(file) for file in input]
        pandas.concat(data, axis=0).to_csv(str(output), index=False)

if KEEP_ALIVE == False :
    onsuccess:
        shell(f"python commons.py stop-virtuoso --config {VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini")
        shell(f"python commons.py stop-fuseki --port {FUSEKI_PORT}")
        shell(f"python commons.py stop-fedup --port {FEDUP_PORT}")
    onerror:
        shell(f"python commons.py stop-virtuoso --config {VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini")
        shell(f"python commons.py stop-fuseki --port {FUSEKI_PORT}")
        shell(f"python commons.py stop-fedup --port {FEDUP_PORT}")