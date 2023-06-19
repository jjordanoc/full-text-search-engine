import psycopg2
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from inverted_index import *
import uvicorn

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE_PATH = "sample.json"
INDEX_NAME = "inverted_index"
STOPLIST_FILE_PATH = "stoplist.txt"


@app.post('/postgresql_recover')
async def obtener_datos(data: dict) -> dict:
    Q = data.get('query')
    k = int(data.get('k')) if data.get('k') != '' else 1

    conn = psycopg2.connect(
        database='db2project2',
        port='5432',
        user='postgres',
        password='postgres'
    )

    cursor = conn.cursor()

    postgreSQL_select = f"""
        SELECT title, abstract, ts_rank(indexed, query) rank
        FROM documents2, plainto_tsquery('english', '{Q}') query
        ORDER BY rank DESC LIMIT {k};
    """

    cursor.execute(postgreSQL_select)
    response = cursor.fetchall()

    conn.close()
    cursor.close()
    return {'data': response}


@app.post('/local_index_recover')
async def get_top_k_invidx(data: dict) -> dict:
    try:
        q = data.get('query')
        k = int(data.get('k')) if data.get('k') != '' else 1
        index = InvertedIndex(raw_data_file_name=DATA_FILE_PATH, index_name=INDEX_NAME,
                              stoplist_file_name=STOPLIST_FILE_PATH)
        query_result = index.cosine_score(query=q, k=k)
        response = index.get_documents_from_query_result(query_result)
        return {'data': response}
    except Exception as e:
        print(e)
        return {'data': None}


@app.post('/create_index')
async def create_index() -> dict:
    index = InvertedIndex(raw_data_file_name=DATA_FILE_PATH, index_name=INDEX_NAME,
                          stoplist_file_name=STOPLIST_FILE_PATH)
    index.create()
    return {'response': 200}


if __name__ == '__main__':
    uvicorn.run('main:app', host='0.0.0.0', reload=True)
