import json
import logging.config
import os
import re
import sys

import mssql_python
import MySQLdb
import psycopg

level = logging.DEBUG
log_filename = "test.log"

logging.basicConfig(level=level, style="{", format="{asctime} - {levelname} - {message}",
                    datefmt="%Y-%m-%d %H:%M",
                    filename=log_filename)

logger = logging.getLogger(__name__)


def mysql_query(config, query, parameters=None):

    with MySQLdb.connect(
        host=config["host"],
        user=config["user"],
        passwd=config["password"],
        db=config["database"],
        port=config["port"]) as conn:

        try:
            with conn.cursor() as cur:
                cur.execute(query, parameters)
                return cur.fetchall()
        except MySQLdb.Error as e:
            logger.debug(f"Error: {e}")
            print(e)


def postgres_query(config, query, parameters=None):
    with psycopg.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"],
        port=config["port"]) as conn:

        try:
            with conn.cursor() as cur:
                cur.execute(query, parameters)
                return cur.fetchall()
        except psycopg.Error as e:
            print(e)

def mssql_query(config, query, parameters=None):

    connection_string = f"""SERVER={config['host']},{config['port']};
DATABASE={config['database']};UID={config['user']};PWD={config['password']};
Encrypt=No;"""
    with mssql_python.connect(connection_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query, parameters)
                return cur.fetchall()
        except mssql_python.Error as e:
            print(e)

envvars = ['DB_TYPE','PROXY_PORT','DB_HOST','DB_USER','DB_PASSWORD','DB_NAME']
for var in envvars:
    if not os.getenv(var):
        logger.debug(f"Please set {var}")
        exit()

debug = os.getenv('DEBUG') and os.getenv('DEBUG').lower() == "true"

config = {
    "dbms": os.getenv('DB_TYPE'),
    "host": os.getenv('DB_HOST'),
    "user": os.getenv('DB_USER'),
    "password": os.getenv('DB_PASSWORD'),
    "database": os.getenv('DB_NAME'),
    "port": int(os.getenv('PROXY_PORT')),
}

if debug:
    print(f"config {config}")

"""
    ["SELECT id, name, password FROM users WHERE id IN (%s, %s) or name=%s", [1,2,"salut"]],
    ["SELECT id, name, password FROM users WHERE id=%(id)s", {'id': 2}],
"""

with open("queries.json", "r", encoding="utf-8") as f:
    all_queries = json.load(f)

queries = []
queries_type = []

if len(sys.argv) == 2:
    queries_type = sys.argv[1].split(",")

print(f"sys.argv {sys.argv}")
print(f"queries_type {queries_type}")

for query_type, queries_arr in all_queries.items():


    print(f"query_type {query_type}")
    print(f"queries_arr {queries_arr}")

    if not queries_type or query_type in queries_type:
        queries.extend(queries_arr)

print(queries)

for query in queries:
    if config['dbms'] in ["mysql", "mariadb"]: res = mysql_query(config, query['query'], query['params'])
    elif config['dbms'] == "postgres": res = postgres_query(config, query['query'], query['params'])
    elif config['dbms'] == "mssql": res = mssql_query(config, query['query'], query['params'])
    
    #if debug:
    print(f"> {query['query']}")
    print(f"< {res}")
    print()
