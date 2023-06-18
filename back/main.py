import psycopg2
from fastapi import FastAPI

from fastapi.middleware.cors import CORSMiddleware
from inverted_index import *

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE_PATH = "test.json"
INDEX_NAME = "inverted_index"
STOPLIST_FILE_PATH = "stoplist.txt"


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
        SELECT title, abstract, ts_rank_cd(indexed, query) rank
        FROM documents2, plainto_tsquery('english', '{Q}') query
        ORDER BY rank DESC LIMIT {k};
    """

    cursor.execute(postgreSQL_select)
    response = cursor.fetchall()

    conn.close()
    cursor.close()
    return {'data': response}


@app.post('/obtener_datos2')
async def get_top_k_invidx(q: str, k: int) -> dict:
    try:
        index = InvertedIndex(raw_data_file_name=DATA_FILE_PATH, index_name=INDEX_NAME,
                              stoplist_file_name=STOPLIST_FILE_PATH)
        response = index.cosine_score(query=q, k=k)
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


def get_top_k_academic(q: str, k: int) -> None:
    index = InvertedIndex(raw_data_file_name=DATA_FILE_PATH, index_name=INDEX_NAME,
                          stoplist_file_name=STOPLIST_FILE_PATH)
    topk = index.cosine_score(q, k)
    print(topk)



# query = "We give a prescription for how to compute the Callias index, using as\nregulator an exponential function.We find agreement with old results in all\nodd dimensions. We show that the problem of computing the dimension ofthe\nmoduli space of self-dual strings can be formulated as an index problem in\neven-dimensional (loop-)space. Wethink that the regulator used in this Letter\ncan be applied to this index problem.\n"
# get_top_k_academic(query, 3)
