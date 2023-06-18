import psycopg2
import json
from os import environ, path
from dotenv import load_dotenv

basedir = path.abspath(path.dirname(__file__))
load_dotenv(path.join(basedir, '.env'))


def postgreSQL_insert_document(id, title, abstract, tablename = 'documents'):
    return f"INSERT INTO {tablename}(id, title, abstract) VALUES ('{id}', '{title}', '{abstract}');"


def create_table(tablename):
    conn = psycopg2.connect(
        host=environ.get('POSTGRES_HOST'),
        database=environ.get('POSTGRES_DATABASE_NAME'),
        port='5432',
        user='postgres',
        password=environ.get('POSTGRES_CONN_PASSWORD')
    )

    cursor = conn.cursor()
    postgreSQL_create_table = f"""CREATE TABLE IF NOT EXISTS {tablename}(
                                    id TEXT, 
                                    title TEXT, 
                                    abstract TEXT
                                    );"""
    cursor.execute(postgreSQL_create_table)

    conn.commit()
    cursor.close()
    conn.close()


def insert_documents(tablename = 'documents'):
    conn = psycopg2.connect(
        host=environ.get('POSTGRES_HOST'),
        database=environ.get('POSTGRES_DATABASE_NAME'),
        port='5432',
        user='postgres',
        password=environ.get('POSTGRES_CONN_PASSWORD')
    )

    cursor = conn.cursor()

    i = 0
    # n = 2272690
    n = 1000000
    with open('../data.json', 'r') as file:
        while i < n:
            line = file.readline()
            document = json.loads(line)

            docid: str = document["id"]
            doctitle: str = document["title"]
            docabstract: str = document["abstract"]

            insert = postgreSQL_insert_document(
                docid.replace('\'', '\'\''),
                doctitle.replace('\'', '\'\''),
                docabstract.replace('\'', '\'\''), 
                tablename=tablename
                )
            cursor.execute(insert)
            i += 1

    conn.commit()
    cursor.close()
    conn.close()


def create_index(tablename='documents'):
    conn = psycopg2.connect(
        host=environ.get('POSTGRES_HOST'),
        database=environ.get('POSTGRES_DATABASE_NAME'),
        port='5432',
        user='postgres',
        password=environ.get('POSTGRES_CONN_PASSWORD')
    )

    cursor = conn.cursor()
    cursor.execute('CREATE EXTENSION IF NOT EXISTS pg_trgm;')

    cursor.execute(f"ALTER TABLE {tablename} ADD COLUMN indexed tsvector;")
    cursor.execute(f"""UPDATE {tablename} SET indexed = T.indexed FROM (
                    SELECT id, setweight(to_tsvector('english', title), 'A') || setweight(to_tsvector('english', abstract), 'B') AS indexed FROM {tablename}
                   ) AS T WHERE {tablename}.id = T.id;""")
    # cursor.execute('CREATE INDEX IF NOT EXISTS abstract_idx_gin ON documents USING gin (indexed);')

    conn.commit()
    cursor.close()
    conn.close()
