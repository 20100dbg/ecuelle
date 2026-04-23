import argparse
import MySQLdb
import psycopg
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
parser.add_argument('--dbms', type=str, choices=["mysql", "postgres", "mssql"], required=True)
parser.add_argument('--host', type=str)
parser.add_argument('--port', type=int)
parser.add_argument('--user', type=str)
parser.add_argument('--password', type=str)
parser.add_argument('--database', type=str)
parser.add_argument('--test', action="store_true", default=False)

args = parser.parse_args()

if not args.host: args.host = "127.0.0.1"
if not args.password: args.password = "my-secret-password123"
if not args.database: args.database = "sample"

if args.dbms == "mysql":
    if not args.port: args.port = 3306
    if not args.user: args.user = "root"

if args.dbms == "postgres":
    if not args.port: args.port = 5432
    if not args.user: args.user = "postgres"

if args.dbms == "mssql":
    if not args.port: args.port = 1422
    if not args.user: args.user = "sa"

config = {
    "host": args.host,
    "user": args.user,
    "password": args.password,
    "database": args.database,
    "port": args.port,
}

if not args.test:

    while True:
        query = input("Query : ")
        if not query and last_query:
            query = last_query

        if args.dbms == "mysql": res = mysql_query(config, query)
        elif args.dbms == "postgres": res = postgres_query(config, query)
        elif args.dbms == "mssql": res = mssql_query(config, query)

        last_query = query
        print(res)

else:

    queries = [
        "SELECT * FROM users;",
        "SELECT * FROM data;",
        "SELECT * FROM NOT_A_TABLE;",
        "SELECT '',0,null"
    ]

    for query in queries:
        if args.dbms == "mysql": res = mysql_query(config, query)
        elif args.dbms == "postgres": res = postgres_query(config, query)
        elif args.dbms == "mssql": res = mssql_query(config, query)
        print(res)
