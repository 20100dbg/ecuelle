import argparse
import psycopg
import MySQLdb
import pyodbc

def run_postgres_query(config, query):
    with psycopg.connect(
        host=config["host"],
        user=config["user"],
        password=config["password"],
        dbname=config["database"],
        port=config["port"]
    ) as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def run_mysql_query(config, query):

    conn = MySQLdb.connect(
        host=config["host"],
        user=config["user"],
        passwd=config["password"],
        db=config["database"],
        port=config["port"]
    )

    try:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()
    except Exception as e:
        print(e)
    finally:
        conn.close()


def run_mssql_query(config, query):
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        f"SERVER={config['host']};"
        f"PORT={config['port']};"
        f"DATABASE={config['database']};"
        f"UID={config['user']};"
        f"PWD={config['password']}"
    )

    conn = pyodbc.connect(conn_str)

    try:
        cur = conn.cursor()
        cur.execute(query)
        rows = cur.fetchall()
        cur.close()
        return rows
    finally:
        conn.close()



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

    if args.dbms == "mysql": res = run_mysql_query(config, query)
    elif args.dbms == "postgres": res = run_postgres_query(config, query)
    elif args.dbms == "mssql": res = run_mssql_query(config, query)

    print(res)