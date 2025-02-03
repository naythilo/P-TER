import os
import pandas
import tempfile

#from snakemake import shell
#from snakemake.io import expand

# Définition des ports des serveurs
VIRTUOSO_PORT = 8890
FUSEKI_PORT = 3030

# Timeout pour chaque requête
TIMEOUT = 1200  # 20 minutes

# Nombre d'exécutions par requête
RUNS = [1, 2, 3]

# Liste des workloads
WORKLOADS = ["rdfs"]

QUERIES = ["q05"]

# Fonction pour récupérer les requêtes SPARQL
def get_queries(workload):
    query_dir = f"queries/{workload}"
    return [os.path.splitext(q)[0] for q in os.listdir(query_dir) if q.endswith(".sparql")]

rule all:
    input:
        expand("output/{workload}/{approach}/{query}.{run}.csv",
            workload=WORKLOADS,
            approach=["Virtuoso", "Fuseki"],
            query=QUERIES,
            run=RUNS)

# Exécuter une requête SPARQL et stocker les résultats
rule run_sparql_query:
    priority: 50
    input:
        query_file = "queries/{workload}/{approach}/{query}.sparql"
    output:
        metrics = "output/{workload}/{approach}/{query}.{run}.csv",
        solutions = "output/{workload}/{approach}/{query}.{run}.json"
    params:
        timeout = TIMEOUT
    run:
        query_tmp = tempfile.NamedTemporaryFile(delete=False)

        # Définition du bon endpoint SPARQL
        endpoint_url = f"http://localhost:{VIRTUOSO_PORT}/sparql" if wildcards.approach == "Virtuoso" else f"http://localhost:{FUSEKI_PORT}/sparql"

        # Modification temporaire du fichier de requête pour utiliser le bon endpoint
        shell(f"sed -E 's@http://localhost:[0-9]+/sparql@{endpoint_url}@g' {input.query_file} > {query_tmp.name}")

        # Exécuter la requête avec un timeout
        shell(f"timeout {params.timeout} python commons.py run-rsa-query {query_tmp.name} --metrics-output {output.metrics} --solutions-output {output.solutions}")

        # Post-traitement des résultats avec Pandas
        df = pandas.read_csv(output.metrics)
        df["query"] = wildcards.query
        df["workload"] = wildcards.workload
        df["approach"] = wildcards.approach
        df["run"] = wildcards.run
        df.to_csv(output.metrics, index=False)

        # Nettoyage du fichier temporaire
        query_tmp.close()
        os.unlink(query_tmp.name)
