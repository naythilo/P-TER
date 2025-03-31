import os
import re
import sys
import time
import json
import click
import signal
import pandas
import requests
import subprocess
import SPARQLWrapper
import subprocess
import shlex
import pandas as pd


def get_pid(port):
    pid = None
    try:
        output = subprocess.check_output(["lsof", "-t", "-i", f":{port}", "-sTCP:LISTEN"])
        pid = int(output.strip())
    except subprocess.CalledProcessError:
        pass
    return pid


def load_query(query_file):
    with open(query_file, "r") as file:
        return file.read()


def load_endpoints(endpoints_file):
    with open(endpoints_file, "r") as file:
        return [str(endpoint).strip() for endpoint in file.readlines()]


def write_solutions(solutions, output):
    if output is not None:
        with open(output, "w") as file:
            file.write(json.dumps(solutions))


def write_metrics(metrics, output):
    if output is not None:
        pandas.DataFrame.from_dict(metrics).to_csv(output)


def send_signal(port, signal):
    pid = get_pid(port)
    if pid is None:
        return
    print(f"Stopping process with pid {pid}")
    os.kill(pid, signal)


@click.group()
def cli():
    pass


@cli.command()
@click.argument("port", type=click.INT)
@click.option("--soft/--kill", type=click.BOOL, default=True)
def stop_process(port, soft):
    send_signal(port, signal.SIGTERM if soft else signal.SIGKILL)


@cli.command()
@click.option("--config", type=click.Path(exists=True, dir_okay=False), default="virtuoso-opensource-7.2.7/var/lib/virtuoso/db/fedup.ini")
@click.option("--restart", type=click.BOOL, default=False)
@click.option("--home", type=click.Path(exists=True, file_okay=False), default="virtuoso-opensource-7.2.7")
def start_virtuoso(config, restart, home):
    with open(config, "r") as file:
        s = file.read().split("[HTTPServer]")[1]
        port = int(re.findall(r"ServerPort\s*=\s([0-9]+)", s)[0])
    if restart:
        send_signal(port, signal.SIGTERM)
    if get_pid(port) is not None:
        print("Virtuoso is running")
        return
    print("running Virtuoso")
    subprocess.Popen(
        [f"{home}/bin/virtuoso-t", "+configfile", config, "+foreground"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    time.sleep(20)


@cli.command()
@click.option("--config", type=click.Path(exists=True, dir_okay=False), default="virtuoso-opensource-7.2.7/var/lib/virtuoso/db/fedup.ini")
@click.option("--soft/--kill", type=click.BOOL, default=True)
def stop_virtuoso(config, soft):
    with open(config, "r") as file:
        s = file.read().split("[HTTPServer]")[1]
        port = int(re.findall(r"ServerPort\s*=\s([0-9]+)", s)[0])
    send_signal(port, signal.SIGTERM if soft else signal.SIGKILL)


@cli.command()
@click.option("--port", type=click.INT, default=3030)
@click.option("--restart", type=click.BOOL, default=False)
@click.option("--home", type=click.Path(exists=True, file_okay=False), default="apache-jena-fuseki-4.9.0")
def start_fuseki(port, restart, home):
    if restart:
        send_signal(port, signal.SIGTERM)
    if get_pid(port) is not None:

        print("Apache Fuseki is running")
        return
    print("running Apache Fuseki")
    command_line_process = subprocess.Popen(
        [f"{home}/fuseki-server", "--mem", "--port", str(port), "/sparql"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    time.sleep(10)


@cli.command()
@click.option("--port", type=click.INT, default=3030)
@click.option("--soft/--kill", type=click.BOOL, default=True)
def stop_fuseki(port, soft):
    send_signal(port, signal.SIGTERM if soft else signal.SIGKILL)


@cli.command()
@click.option("--port", type=click.INT, default=8080)
@click.option("--restart", type=click.BOOL, default=False)
def start_fedup(port, restart):
    if restart:
        send_signal(port, signal.SIGTERM)
    if get_pid(port) is not None:
        print("FedUP is running")
        return
    print("running FedUP")
    subprocess.Popen([
            "mvn", "spring-boot:run", "-pl", "fedup",
            f"-Dserver.port={port}"
            " -Dspring-boot.run.jvmArguments=\"-Xms4096M -Xmx8192M -XX:TieredStopAtLevel=4\""],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL)
    time.sleep(10)


@cli.command()
@click.option("--port", type=click.INT, default=8080)
@click.option("--soft/--kill", type=click.BOOL, default=True)
def stop_fedup(port, soft):
    send_signal(port, signal.SIGTERM if soft else signal.SIGKILL)


@cli.command()
@click.argument("query", type=click.Path(exists=True, dir_okay=False))
@click.option("--port", type=click.INT, default=3030)
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
def run_rsa_query(query, port, metrics_output, solutions_output):
    print(port)
    sparql = SPARQLWrapper.SPARQLWrapper(f"http://localhost:{port}/sparql/")
    sparql.setReturnFormat(SPARQLWrapper.JSON)
    sparql.setQuery(load_query(query))

    try:
        start_time = time.time()
        solutions = sparql.queryAndConvert()
        print("hey")
        print(solutions)
        #print(sparql.query.encode("utf-8"))


        end_time = time.time()
        metrics = {
            "status": ["ok"],
            "reason": [None],
            "sourceSelectionTime": [0],
            "executionTime": [(end_time - start_time) * 1000],
            "runtime": [(end_time - start_time) * 1000],
            "numASKQueries": [0],
            "numSolutions": [len(solutions["results"]["bindings"])],
            "numAssignments": [0],
            "tpwss": [0]
        }
    except Exception as error:
        metrics = {"status": ["error"], "reason": [error]}
        solutions = []
    print(f"solutions: {solutions}")
    print((end_time - start_time) * 1000)
    write_metrics(metrics, metrics_output)
    write_solutions(solutions, solutions_output)

    sys.exit(0 if metrics["status"][0] == "ok" else 1)


@cli.command()
@click.argument("query", type=click.Path(exists=True, dir_okay=False))
@click.argument("endpoints", type=click.Path(exists=True, dir_okay=False))
@click.argument("config", type=click.Path(exists=True, dir_okay=False))
@click.option("--port", type=click.INT, default=8080)
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
def run_query(query, endpoints, config, port, metrics_output, solutions_output):
    
    def signal_handler(signal, frame):  # used to handle the signal sent by the timeout command
        write_metrics({"status": ["timeout"], "reason": [None]}, metrics_output)
        write_solutions([], solutions_output)
        sys.exit(124)

    signal.signal(signal.SIGTERM, signal_handler)

    try:
        response = requests.post(f"http://localhost:{port}/fedSparql", json={
            "queryString": load_query(query),
            "configFileName": config,
            "endpoints": load_endpoints(endpoints),
            "runQuery": True
        })
        result = json.loads(response.content.decode("utf-8"))
        metrics = {k: [v] for k, v in result.items() if k in [
            "sourceSelectionTime",
            "executionTime",
            "runtime",
            "numASKQueries",
            "numSolutions",
            "numAssignments",
            "tpwss"
        ]} | {"status": ["ok"], "reason": [None]}
        solutions = result["solutions"]
    except Exception as error:
        metrics = {"status": ["error"], "reason": [error]}
        solutions = []

    write_metrics(metrics, metrics_output)
    write_solutions(solutions, solutions_output)

    sys.exit(0 if metrics["status"] == "ok" else 1)


@cli.command()
@click.argument("query_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
def run_jena_query(query_file,metrics_output,solutions_output):
    #Execute Query
    command = ["./apache-jena-4.9.0/bin/sparql", "--query", query_file, "--time", "--results=JSON"]
    result = subprocess.run(command, capture_output=True, text=True)

    #CSV Data
    time_match = re.search(r"Time: (\d+\.\d+) sec", result.stderr)
    execution_time = time_match.group(1) if time_match else "N/A"
    results = result.stdout

    try:
        results_json = json.loads(result.stdout)
        bindings = results_json.get("results", {}).get("bindings", [])
        num_results = len(bindings)  # Nombre de résultats dans "bindings"
    except json.JSONDecodeError:
        num_results = 0

    df = pd.DataFrame([{"status": "ok", "TotalExecutionTime": execution_time,"nbResult":num_results,"planningTime":0,"executionTime":execution_time}])

    df.to_csv(metrics_output, index=False)

    #Json Data
    write_solutions(result.stdout, solutions_output)


@cli.command()
@click.argument("query_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
@click.option("--err-output", type=click.Path())
def run_hefquin_query(query_file,metrics_output,solutions_output,err_output):
    #Execute Query
    os.chdir("../HeFQUIN-FRAW")
    command = ["./bin/hefquin", "--federationDescription fedshop200.ttl","--confDescr DefaultEngineConfForRSA.ttl", "--file", query_file, "--time", "--results=JSON","--printQueryProcStats"]
    result = subprocess.run(command, capture_output=True, text=True)
    os.chdir("../P-TER")

    with open(err_output, "w") as file:
        file.write(result.stdout + result.stderr)

    #CSV & Json data

    time_match = re.search(r"Time: (\d+\.\d+) sec", result.stderr)

    execution_time = time_match.group(1) if time_match else "N/A"

    results = result.stdout
    try:
        results_json = json.loads(results)
        bindings = results_json.get("results", {}).get("bindings", [])
        num_results = len(bindings)  
    except json.JSONDecodeError:
        num_results = 0

    df = pd.DataFrame([{"status": "ok", "TotalExecutionTime": execution_time,"nbResult":num_results,"planningTime":0,"executionTime":execution_time}])

    df.to_csv(metrics_output, index=False)

    write_solutions(results, solutions_output)


@cli.command()
@click.argument("query_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
@click.option("--err-output", type=click.Path())
def run_fedup_fedx_query(query_file, metrics_output, solutions_output, err_output):
    # Execute Query with a timeout of 30 seconds
    command = [
        "java", "-Xmx12g", "-jar", "../fedup/target/fedup.jar", 
        "-e", "FedX", 
        "-f", query_file, 
        "-s", "/workspaces/P-TER/fedshop200-h0", 
        "-x",
        "-m", "(e) -> \"http://localhost:8890/sparql?default-graph-uri=\" + e.substring(0, e.length())"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)  
    except subprocess.TimeoutExpired:
        # Timeout occurred, return null data
        with open(err_output, "w") as file:
            file.write("Timeout exceeded 180 seconds.\n")
        
        # Write null values to CSV and JSON
        df = pd.DataFrame([{
            "status": "timeout", 
            "TotalExecutionTime": None,
            "nbResult": None,
            "planningTime": None,
            "executionTime": None,
        }])
        df.to_csv(metrics_output, index=False)

        json_data = json.dumps([], indent=4)
        write_solutions(json_data, solutions_output)

        return  # Exit the function after handling timeout

    # If no timeout occurred, proceed as usual
    with open(err_output, "w") as file:
        file.write(result.stderr + result.stdout)

    # CSV Data
    time_match = re.search(r"Took (\d+) ms to retrieve (\d+) mappings", result.stderr)
    time_match_source_assignment = re.search(r"Took (\d+) to perform the source assignment", result.stderr)

    if time_match:
        retrieval_time = int(time_match.group(1))
        retrieval_time = retrieval_time / 1000
        nbResult = time_match.group(2)   
    else:
        retrieval_time = "N/A"
        nbResult = "N/A"

    if time_match_source_assignment: 
        retrieval_time_source_assignment = int(time_match_source_assignment.group(1))
        retrieval_time_source_assignment = retrieval_time_source_assignment / 1000
    else: 
        retrieval_time_source_assignment = "N/A"

    if retrieval_time == "N/A" or retrieval_time_source_assignment == "N/A":
        totalexectime = None
    else:
        totalexectime = str(float(retrieval_time) + float(retrieval_time_source_assignment))

    df = pd.DataFrame([{
        "status": "ok", 
        "TotalExecutionTime": totalexectime,
        "nbResult": nbResult,
        "planningTime": retrieval_time_source_assignment,
        "executionTime": retrieval_time,
    }])

    df.to_csv(metrics_output, index=False)

    # JSON Data
    pattern = r'\( \?([^=]+) = (?:<([^>]+)>)?\s*(?:"([^"]+)"(\^\^[a-zA-Z0-9:]+)?)? \)'

    matches = re.findall(pattern, result.stdout)

    data = []
    for match in matches:
        value = match[2] if match[2] else ''
        
        # Si le type de données (^^) existe, ajoute-le à la valeur
        if match[3]:  
            value += match[3]
        
        # Si une URL existe, associe-la avec la clé correspondante
        if match[1]:
            data.append({match[0]: match[1], 'value': value})
        else:
            data.append({match[0]: value})

    # Conversion en JSON
    json_data = json.dumps(data, indent=4)
    write_solutions(json_data, solutions_output)




@cli.command()
@click.argument("query_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
@click.option("--err-output", type=click.Path())
def run_fedup_jena_query(query_file, metrics_output, solutions_output, err_output):
    # Execute Query with a timeout of 30 seconds
    command = [
        "java", "-Xmx12g", "-jar", "../fedup/target/fedup.jar", 
        "-e", "Jena", 
        "-f", query_file, 
        "-s", "/workspaces/P-TER/fedshop200-h0", 
        "-x",
        "-m", "(e) -> \"http://localhost:8890/sparql?default-graph-uri=\" + e.substring(0, e.length())"
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)  
    except subprocess.TimeoutExpired:
        # Timeout occurred, return null data
        with open(err_output, "w") as file:
            file.write("Timeout exceeded 180 seconds.\n")
        
        # Write null values to CSV and JSON
        df = pd.DataFrame([{
            "status": "timeout", 
            "TotalExecutionTime": None,
            "nbResult": None,
            "planningTime": None,
            "executionTime": None,
        }])
        df.to_csv(metrics_output, index=False)

        json_data = json.dumps([], indent=4)
        write_solutions(json_data, solutions_output)

        return  # Exit the function after handling timeout

    # If no timeout occurred, proceed as usual
    with open(err_output, "w") as file:
        file.write(result.stderr + result.stdout)

    # CSV Data
    time_match = re.search(r"Took (\d+) ms to retrieve (\d+) mappings", result.stderr)
    time_match_source_assignment = re.search(r"Took (\d+) to perform the source assignment", result.stderr)

    if time_match:
        retrieval_time = int(time_match.group(1))
        retrieval_time = retrieval_time / 1000
        nbResult = time_match.group(2)   
    else:
        retrieval_time = "N/A"
        nbResult = "N/A"

    if time_match_source_assignment: 
        retrieval_time_source_assignment = int(time_match_source_assignment.group(1))
        retrieval_time_source_assignment = retrieval_time_source_assignment / 1000
    else: 
        retrieval_time_source_assignment = "N/A"

    if retrieval_time == "N/A" or retrieval_time_source_assignment == "N/A":
        totalexectime = None
    else:
        totalexectime = str(float(retrieval_time) + float(retrieval_time_source_assignment))

    df = pd.DataFrame([{
        "status": "ok", 
        "TotalExecutionTime": totalexectime,
        "nbResult": nbResult,
        "planningTime": retrieval_time_source_assignment,
        "executionTime": retrieval_time,
    }])

    df.to_csv(metrics_output, index=False)

    # JSON Data
    pattern = r'\( \?([^=]+) = (?:<([^>]+)>)?\s*(?:"([^"]+)"(\^\^[a-zA-Z0-9:]+)?)? \)'

    matches = re.findall(pattern, result.stdout)

    data = []
    for match in matches:
        value = match[2] if match[2] else ''
        
        # Si le type de données (^^) existe, ajoute-le à la valeur
        if match[3]:  
            value += match[3]
        
        # Si une URL existe, associe-la avec la clé correspondante
        if match[1]:
            data.append({match[0]: match[1], 'value': value})
        else:
            data.append({match[0]: value})

    # Conversion en JSON
    json_data = json.dumps(data, indent=4)
    write_solutions(json_data, solutions_output)
    

@cli.command()
@click.argument("query_file", type=click.Path(exists=True, dir_okay=False))
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
@click.option("--err-output", type=click.Path())
def run_fedup_hefquin_query(query_file, metrics_output, solutions_output, err_output):
    hefquin_directory = "../HeFQUIN-FRAW"
    
    # Change directory to HeFQUIN folder
    os.chdir(hefquin_directory)
    
    # Command to execute
    command = [
        "./bin/hefquin", "--federationDescription", "fedshop200.ttl",
        "--confDescr", "DefaultEngineWithFedupConfForFedshop200.ttl", 
        "--file", query_file, "--time", "--results=JSON", "--printQueryProcStats"
    ]
    
    try:
        #result = subprocess.run(command, capture_output=True, text=True) 
        #print("youhou")
        #time.sleep(5) 
        result = subprocess.run(command, capture_output=True, text=True, timeout=180)  
    except subprocess.TimeoutExpired:
        
        os.chdir("../P-TER")
        # Timeout occurred, return null data
        with open(err_output, "w") as file:
            file.write("Timeout exceeded 180 seconds.\n")
        
        # Write null values to CSV and JSON
        df = pd.DataFrame([{
            "status": "timeout", 
            "TotalExecutionTime": None,
            "nbResult": None,
            "planningTime": None,
            "executionTime": None,
        }])
        df.to_csv(metrics_output, index=False)

        json_data = json.dumps([], indent=4)
        write_solutions(json_data, solutions_output)
        
        command2 = [
        "killall", "-9", "java"
    ]
        resultda = subprocess.run(command2, capture_output=True, text=True)
        
        
        return  # Exit the function after handling timeout

    # Change back to the original directory (P-TER)
    os.chdir("../P-TER")
    
    # Write stderr and stdout to the error output file
    with open(err_output, "w") as file:
        file.write(result.stderr + result.stdout)
    
    # CSV data extraction
    time_match = re.search(r"Time: (\d+\.\d+) sec", result.stderr)
    time_match_planningTime = re.search(r"planningTime\s*:\s*(\d+)", result.stderr)
    time_match_executionTime = re.search(r"executionTime\s*:\s*(\d+)", result.stderr)

    execution_time = time_match.group(1) if time_match else "N/A"

    if time_match_executionTime:
        retrieval_time = int(time_match_executionTime.group(1)) / 1000
    else:
        retrieval_time = "N/A"

    if time_match_planningTime:
        retrieval_time_source_assignment = int(time_match_planningTime.group(1)) / 1000
    else:
        retrieval_time_source_assignment = "N/A"

    if time_match is None:
        retrieval_time = "N/A"
        nbResult = "N/A"
    
    try:
        results_json = json.loads(result.stdout)
        bindings = results_json.get("results", {}).get("bindings", [])
        num_results = len(bindings)  # Nombre de résultats dans "bindings"
    except json.JSONDecodeError:
        num_results = 0

    # Write the metrics to the CSV file
    df = pd.DataFrame([{
        "status": "ok", 
        "TotalExecutionTime": execution_time,
        "nbResult": num_results,
        "planningTime": retrieval_time_source_assignment,
        "executionTime": retrieval_time,
    }])

    df.to_csv(metrics_output, index=False)

    # Write the JSON data to the solutions output file
    write_solutions(result.stdout, solutions_output)


if __name__ == "__main__":
    cli()