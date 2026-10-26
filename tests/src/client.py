import MySQLdb
import psycopg
import mssql_python
import os
import logging.config

level = logging.DEBUG
log_filename = "test.log"

logging.basicConfig(level=level, style="{", format="{asctime} - {levelname} - {message}",
                    datefmt="%Y-%m-%d %H:%M",
                    filename=log_filename)

logger = logging.getLogger(__name__)


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
            logger.debug(f"Error: {e}")
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

    connection_string = f"""SERVER={config['host']},{config['port']};
DATABASE={config['database']};UID={config['user']};PWD={config['password']};
Encrypt=No;"""
    with mssql_python.connect(connection_string) as conn:
        try:
            with conn.cursor() as cur:
                cur.execute(query)
                return cur.fetchall()
        except Exception as e:
            print(e)




if not os.getenv('DB_TYPE'):
    logger.debug("Please set DB_TYPE")
    raise ValueError("Missing DB_TYPE parameter")

if not os.getenv('PROXY_PORT'):
    logger.debug("Please set PROXY_PORT")
    raise ValueError("Missing PROXY_PORT parameter")

if not os.getenv('DB_HOST'):
    logger.debug("Please set DB_HOST")
    raise ValueError("Missing DB_HOST parameter")

if not os.getenv('DB_USER'):
    logger.debug("Please set DB_USER")
    raise ValueError("Missing DB_USER parameter")

if not os.getenv('DB_PASSWORD'):
    logger.debug("Please set DB_PASSWORD")
    raise ValueError("Missing DB_PASSWORD parameter")

if not os.getenv('DB_NAME'):
    logger.debug("Please set DB_NAME")
    raise ValueError("Missing DB_NAME parameter")

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

queries = [
    "SELECT * FROM users;",
    "SELECT * FROM data;",
    "SELECT * FROM NOT_A_TABLE;",
    "SELECT '',0,null"
]

for query in queries:
    if config['dbms'] in ["mysql", "mariadb"]: res = mysql_query(config, query)
    elif config['dbms'] == "postgres": res = postgres_query(config, query)
    elif config['dbms'] == "mssql": res = mssql_query(config, query)
    
    #if debug:
    print(f"query {query}")
    print(f"result {res}")
