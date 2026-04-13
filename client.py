import argparse
import MySQLdb
import psycopg
#import pyodbc
import mssql_python


def mysql_query(config, query):

    with MySQLdb.connect(
        host=config["host"],
        user=config["user"],
        passwd=config["password"],
        db=config["database"],
        port=config["port"]) as conn:

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)


def postgres_query(config, query):
    with psycopg.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"],
        port=config["port"]) as conn:

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)

"""
def mssql_query(config, query):
    with pyodbc.connect("DRIVER={ODBC Driver 18 for SQL Server};"
        f"SERVER={config['host']};"
        f"PORT={config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};"
        f"PWD={config['password']};"
        f"Encrypt=No") as conn:

        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)
"""

def mssql_query(config, query):

    connection_string = f"SERVER={config['host']},{config['port']};DATABASE={config['database']};UID={config['user']};PWD={config['password']};Encrypt=No;"
    with mssql_python.connect(connection_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)


parser = argparse.ArgumentParser(description='')
parser.add_argument('--dbms', type=str, required=True)
parser.add_argument('--host', type=str, required=True)
parser.add_argument('--port', type=int, required=True)
parser.add_argument('--user', type=str, required=True)
parser.add_argument('--password', type=str, required=True)
parser.add_argument('--database', type=str, required=True)

args = parser.parse_args()

config = {
    "host": args.host,
    "user": args.user,
    "password": args.password,
    "database": args.database,
    "port": args.port,
}

while True:
    
    query = input("Query : ")

    if args.dbms == "mysql": res = mysql_query(config, query)
    elif args.dbms == "postgres": res = postgres_query(config, query)
    elif args.dbms == "mssql": res = mssql_query(config, query)

    print(res)