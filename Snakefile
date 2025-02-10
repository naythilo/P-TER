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
RESTART = False
WORKLOADS = ["rdfs"]
APPROACHES = ["Fuseki"]
QUERIES = ["q05-copy"]

# VARS DE CONFIG DU SNAKEFILE
DO_INSTALL = False
KEEP_ALIVE = False
RUN_QUERY = True
SETUP_VIRTU = False 

# Fonction pour récupérer les requêtes SPARQL
def get_queries(workload):
    query_dir = f"queries/{workload}"
    return [os.path.splitext(q)[0] for q in os.listdir(query_dir) if q.endswith(".sparql")]

rule all:
    input:
        directory(FUSEKI_HOME),
        directory(JENA_HOME),     
        "config/largerdfbench/graphs.txt",
        "config/rdfs/endpoints.txt",
        "hello.txt",
        #bench = expand("output/{workload}/{approach}/{query}.{run}.csv",
        #    workload=WORKLOADS,
        #    approach=APPROACHES,
         #   query=QUERIES,
         #   run=RUNS),
    #output: "output/data.csv"
    #run:
        #data = [pandas.read_csv(file) for file in input.bench]
        #pandas.concat(data,axis=0).to_csv(str(output))
        #expand(
        #    "config/{workload}/endpoints.txt",
        #    workload=["rdfs"]  # Ajoutez d'autres workloads si nécessaire
        #),


         


if DO_INSTALL:

    rule install_apache_jena_fuseki:
            priority: 100
            output: directory(FUSEKI_HOME)
            shell:
                """
                echo "Downloading Apache Jena Fuseki..."
                wget https://archive.apache.org/dist/jena/binaries/apache-jena-fuseki-4.9.0.tar.gz
                echo "Extracting Apache Jena Fuseki..."
                tar -zxf apache-jena-fuseki-4.9.0.tar.gz
                """

    rule install_apache_jena:
        priority: 100
        output:
            jena = directory(JENA_HOME),
            jena_loader = f"{JENA_HOME}/bin/tdb2.xloader"
        shell:
            """
            echo "Downloading Apache Jena ..."
            wget https://archive.apache.org/dist/jena/binaries/apache-jena-4.9.0.tar.gz
            echo "Extracting Apache Jena ..."
            tar -zxf apache-jena-4.9.0.tar.gz
            """

    rule install_virtuoso:
        priority: 100
        output:
            virtuoso = directory(VIRTUOSO_HOME),
            virtuoso_isql = f"{VIRTUOSO_HOME}/bin/isql",
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/virtuoso.ini"
        shell:
            """
            echo "Downloading Virtuoso..."
            wget https://github.com/openlink/virtuoso-opensource/releases/download/v7.2.7/virtuoso-opensource-7.2.7.tar.gz
            echo "Extracting Virtuoso..."
            tar -zxf virtuoso-opensource-7.2.7.tar.gz
            echo "Configuring Virtuoso..."
            cd virtuoso-opensource-7.2.7
            ./autogen.sh
            ./configure --prefix={VIRTUOSO_HOME}
            echo "Building and installing Virtuoso..."
            make && make install && make clean && make distclean
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
            sed -i -E 's@^;(NumberOfBuffers.*?= 170000.*$)@\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@^;(MaxDirtyBuffers.*?= 130000.*$)@\\1@g' {output.virtuoso_configfile}
            sed -i -E 's@(^MaxQueryMem.*)@MaxQueryMem = 2G@g' {output.virtuoso_configfile}
            """


    rule download_datasets:
        output: "datasets/fedshop-virtuoso.db"
        shell:
            """
            gdown https://zenodo.org/records/12204740/files/fedshop-virtuoso.db?download=1 -O datasets/fedshop-virtuoso.db
            """
    
    rule load_LargeRDFBench_into_Virtuoso:
        priority: 100
        input:
            dataset = "datasets/fedshop-virtuoso.db",
            virtuoso = VIRTUOSO_HOME,
            virtuoso_isql = f"{VIRTUOSO_HOME}/bin/isql",
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini"
        output:
            graphs = "config/largerdfbench/graphs.txt"
        shell:
            """
            python commons.py start-virtuoso --home {input.virtuoso} --config {input.virtuoso_configfile}
            {input.virtuoso_isql} "EXEC=ld_dir('`pwd`/datasets', 'fedshop-virtuoso.db', 'NULL');"
            {input.virtuoso_isql} "EXEC=rdf_loader_run();"
            {input.virtuoso_isql} "EXEC=checkpoint;"
            {input.virtuoso_isql} "EXEC=SPARQL SELECT DISTINCT ?g WHERE {{ GRAPH ?g {{ ?s a ?c }} }};" > {output.graphs}
            # python commons.py stop-virtuoso --config {input.virtuoso_configfile}
            """

    rule generate_endpoints:
        input:
            graphs = "config/largerdfbench/graphs.txt"
        output:
            endpoints = "config/rdfs/endpoints.txt"
        shell:
            f"sed -E 's@(^.*$)@http://localhost:{VIRTUOSO_PORT}/sparql?default-graph-uri=\\1@g' {input.graphs} > {output.endpoints}"


if RUN_QUERY:
    

    rule run_sparql_query:
        priority: 50
        input:
            virtuoso = VIRTUOSO_HOME,
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini",
            fuseki = FUSEKI_HOME,
            query_file = "queries/{workload}/Fuseki/{query}.sparql",
            endpoints = "config/rdfs/endpoints.txt",

        output:
            metrics = "output/{workload}/Fuseki/{query}.{run}.csv",
            solutions = "output/{workload}/Fuseki/{query}.{run}.json"
        params:
            timeout = TIMEOUT
        run:
            query_tmp = tempfile.NamedTemporaryFile(delete=False)

            # Définition du bon endpoint SPARQL
            endpoint_url = f"http://localhost:3030/sparql"
            shell(f"python commons.py start-virtuoso --home {{input.virtuoso}} --config {{input.virtuoso_configfile}} --restart {RESTART}")
            shell(f"python commons.py start-fuseki --home {{input.fuseki}} --port {FUSEKI_PORT} --restart {RESTART}")
            # Modification temporaire du fichier de requête pour utiliser le bon endpoint
            shell(f"sed -E 's@http://localhost:[0-9]+/sparql@{endpoint_url}@g' {input.query_file} > {query_tmp.name}")

            # Exécuter la requête avec un timeout
            shell(f"timeout {params.timeout} python commons.py run-rsa-query {query_tmp.name} --metrics-output {output.metrics} --solutions-output {output.solutions}")

            # Post-traitement des résultats avec Pandas
            df = pandas.read_csv(output.metrics)
            df["query"] = wildcards.query
            df["workload"] = wildcards.workload
            #df["approach"] = wildcards.approach
            df["run"] = wildcards.run
            df.to_csv(output.metrics, index=False)

            # Nettoyage du fichier temporaire
            query_tmp.close()
            os.unlink(query_tmp.name)

    rule run_fedX_query:
        priority: 50
        input:
            virtuoso = VIRTUOSO_HOME,
            virtuoso_configfile = f"{VIRTUOSO_HOME}/var/lib/virtuoso/db/fedup.ini",
            fuseki = FUSEKI_HOME,
           # query_file = "queries/{workload}/Fuseki/{query}.sparql",
            endpoints = "config/rdfs/endpoints.txt",
        output: "hello.txt"
        params:
            timeout = TIMEOUT
        run:
            query_tmp = tempfile.NamedTemporaryFile(delete=False)

            # Définition du bon endpoint SPARQL
            shell(f"python commons.py start-virtuoso --home {{input.virtuoso}} --config {{input.virtuoso_configfile}} --restart {RESTART}")

            # Exécuter la requête avec un timeout
            shell(f" /usr/bin/env /opt/java/11.0.14/bin/java @/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile org.example.Virtuoso --input queries/rdfs/Fuseki/q05.sparql")

            shell(f"echo 'hello' > {output}")



#/usr/bin/env /opt/java/11.0.14/bin/java @/tmp/cp_epia4f4tkru96q17baqr1dz53.argfile org.example.Virtuoso --input queries/rdfs/Fuseki/q05.sparql



