import nltk
import numpy as np
from nltk.stem.snowball import SnowballStemmer
import re
import json
from nltk.tokenize import RegexpTokenizer
from typing import List

import os

nltk.download('punkt')

stemmer = SnowballStemmer('english')

tokenizer = RegexpTokenizer(r'[a-zA-ZÀ-ÿ]+')

stopwords = open("back\stoplist.txt","r",encoding="utf-8")
lower_stopword_list = [tk.lower() for tk in tokenizer.tokenize(stopwords.read())]
stopwords = set(lower_stopword_list)


def preprocesamiento(texto):
  # tokenizar
  lower_token_list = [tk.lower() for tk in tokenizer.tokenize(texto)]
  # filtrar stopwords y contar
  tokens_count = dict()
  for tk in lower_token_list:
    if tk not in stopwords:
        if tk in tokens_count:
            tokens_count[tk] += 1
        else:
            tokens_count[tk] = 1
  # reducir palabras y agrupar
  stemmed_tokens_count = dict()
  for tk in tokens_count:
    stemmed = stemmer.stem(tk)
    if stemmed in stemmed_tokens_count:
        stemmed_tokens_count[stemmed] += tokens_count[tk]
    else:
        stemmed_tokens_count[stemmed] = tokens_count[tk]
  return stemmed_tokens_count



class InvertedIndex:

    def __init__(self, collection_path: str, filename: str = "myindex"):
        self.doc_map_file_name = filename + "_docmap.invidx"
        self.index_file_name = filename + "_index.invidx"
        self.idf_file_name = filename + "_idf.invidx"
        self.length_file_name = filename + "_length.invidx"
        self.collection_path = collection_path

    """
        Preprocess all documents, and create a temporary
        file containing the following information:
        (term, doc_id, term_frequency) #doc_id: posicion logica
    """
    def _preprocess(self):
        with open("back\\test.json") as file:
            header_file = open("back\header.txt",mode="w")
            token_stream_file = open("back\\token_stream.txt",mode="w")
            logicPos = 1
            longitud = 0
            while True:
                line = file.readline()
                if not line:
                    header_file.close()
                    token_stream_file.close()
                    break
                posicion_logica = str(logicPos).ljust(8)
                longitud += len(line)
                posicion_fisica = str(longitud)
                
                # Just if we know exactly the quantity of docs to avoid writing skip line at the end of header_file
                docs = 50
                if logicPos == docs:
                    header_file.write(f"{posicion_logica}{posicion_fisica}")
                else:
                    header_file.write(f"{posicion_logica}{posicion_fisica}\n")
                
                line = json.loads(line)

                documento_procesado = preprocesamiento(line["abstract"])

                documento_procesado = dict(sorted(documento_procesado.items(), key=lambda x: x[0],reverse=False))

                # Just if we know exactly the quantity of docs to avoid writing skip line at the end of token_stream_file
                if logicPos == docs:
                    for key in documento_procesado:
                        if key == list(documento_procesado)[-1]:
                            token_stream_file.write(f"({key},{logicPos},{documento_procesado[key]})")
                        else:
                            token_stream_file.write(f"({key},{logicPos},{documento_procesado[key]})\n")
                else:
                    for key in documento_procesado:
                        token_stream_file.write(f"({key},{logicPos},{documento_procesado[key]})\n")

                logicPos += 1



    def _merge_blocks(self, blocks: List[str]):
        block_buffers: List = []
        for i in range(len(blocks)):
            with open(blocks[i]) as local_index:
                pass
        pass

    """
        Build the inverted index file with the collection using
        Single Pass In-Memory Indexing
    """
    def create(self):

        for file in os.listdir(self.collection_path):
            filename = os.fsdecode(file)
            if filename.endswith(".asm") or filename.endswith(".py"):
                # print(os.path.join(directory, filename))
                continue
            else:
                continue

        with open(self.collection_path) as file:
            pass
        pass


def main():
    
    mindicio = InvertedIndex("xednIdetrevnI")
    mindicio._preprocess()

main()

