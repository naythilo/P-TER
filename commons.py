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
from pip._internal import cli

def load_query(query_file):
    with open(query_file, "r") as file:
        return str(file.read())

def write_solutions(solutions, output):
    if output is not None:
        with open(output, "w") as file:
            file.write(json.dumps(solutions))


def write_metrics(metrics, output):
    if output is not None:
        pandas.DataFrame.from_dict(metrics).to_csv(output)

@click.group()
def cli():
    pass

@cli.command()
@click.argument("query", type=click.Path(exists=True, dir_okay=False))
@click.option("--port", type=click.INT, default=3030)
@click.option("--metrics-output", type=click.Path())
@click.option("--solutions-output", type=click.Path())
def run_rsa_query(query, port, metrics_output, solutions_output):
    sparql = SPARQLWrapper.SPARQLWrapper(f"http://localhost:{port}/sparql")

    sparql.setReturnFormat(SPARQLWrapper.JSON)
    sparql.setQuery(load_query(query))

    try:
        start_time = time.time()
        solutions = sparql.queryAndConvert()
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

    write_metrics(metrics, metrics_output)
    write_solutions(solutions, solutions_output)

    sys.exit(0 if metrics["status"] == "ok" else 1)

if __name__ == "__main__":
    cli()