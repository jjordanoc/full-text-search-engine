import psycopg2
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
import sys
sys.path.append('../')

from inverted_index import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post('/obtener_datos')
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
        FROM documents, plainto_tsquery('english', '{Q}') query
        WHERE indexed @@ query ORDER BY rank DESC LIMIT {k};
    """
    
    cursor.execute(postgreSQL_select)
    response = cursor.fetchall()

    conn.close()
    cursor.close()
    return {'data': response}

@app.post('obtener_datos2')
async def get_top_k_academic(Q: str, k: int) -> dict:
    mindicio = InvertedIndex(raw_data_file_name="test.json", index_name="inverted_index",
                             stoplist_file_name="stoplist.txt")
    mindicio.create()
    response = mindicio._cosine_score(Q, k)
    return {'data': response}


def get_top_k_academic(Q: str, k: int) -> dict:
    mindicio = InvertedIndex(raw_data_file_name="test.json", index_name="inverted_index",
                             stoplist_file_name="stoplist.txt")
    mindicio.create()
    topk = mindicio._cosine_score(Q, k)
    print(topk)


query = "We give a prescription for how to compute the Callias index, using as\nregulator an exponential function. We find agreement with old results in all\nodd dimensions. We show that the problem of computing the dimension of the\nmoduli space of self-dual strings can be formulated as an index problem in\neven-dimensional (loop-)space. We think that the regulator used in this Letter\ncan be applied to this index problem.\n"
get_top_k_academic(query, 3)