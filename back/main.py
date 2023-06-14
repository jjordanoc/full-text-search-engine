import nltk
import numpy as np
from nltk.stem.snowball import SnowballStemmer
import re
import json
from ast import literal_eval
from nltk.tokenize import RegexpTokenizer
from typing import List
import sys
import os
from typing import List, TextIO, Tuple, Optional
from Heap import MinHeap

# Unused
MAX_MEMORY_AVAILABLE = 256000000 #256MB
# Used in SPIMI
MAX_TERM_AVAILABLE = 1000 #1000000
# Stemmer for reducing english words into their word stem
stemmer = SnowballStemmer('english')
# Filter to just accept words with normal letter, capital letter and also tildes
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
                posicion_fisica = str(longitud)           
                # Just if we know exactly the quantity of docs to avoid writing skip line at the end of header_file
                docs = 10000000
                if logicPos == docs:
                    header_file.write(f"{posicion_logica}{posicion_fisica}")
                else:
                    header_file.write(f"{posicion_logica}{posicion_fisica}\n")
                longitud += len(line)
                line = json.loads(line)
                documento_procesado = preprocesamiento(line["abstract"])
                documento_procesado = dict(sorted(documento_procesado.items(), key=lambda x: x[0],reverse=False))
                # Just if we know exactly the quantity of docs to avoid writing skip line at the end of token_stream_file
                if logicPos == docs:
                    for key in documento_procesado:
                        if key == list(documento_procesado)[-1]:
                            token_stream_file.write(f"('{key}',{logicPos},{documento_procesado[key]})")
                        else:
                            token_stream_file.write(f"('{key}',{logicPos},{documento_procesado[key]})\n")
                else:
                    for key in documento_procesado:
                        token_stream_file.write(f"('{key}',{logicPos},{documento_procesado[key]})\n")

                logicPos += 1
        # Name's file where is the information as (term, doc_id, term_frequency)
        return "back\\token_stream.txt"


    def merge_blocks(self, blocks: List[str]) -> None:
        outfile = open(self.index_file_name, "w")
        min_heap = MinHeap[Tuple]()
        k: int = len(blocks)
        # Buffer of BLOCK_SIZE to hold elements of each
        block_files: List[TextIO] = []
        # Open all block files and extract initialize min heap of size k
        for i in range(k):
            block_files.append(open(blocks[i]))
            # min_term_tuple: (term, postings_list)
            min_term_tuple = literal_eval(block_files[i].readline())
            # heap elements: (term, block, postings_list)
            min_heap.push((min_term_tuple[0], i, min_term_tuple[1]))
        # Combine all posting lists of the current lowest term
        last_min_term: Optional[Tuple] = None
        while not min_heap.empty():
            # Grab the lowest term from the priority queue
            min_term_tuple = min_heap.pop()
            # If the term is equal to the current lowest, concatenate their posting lists
            if last_min_term and last_min_term[0] == min_term_tuple[0]:
                last_min_term[2].extend(min_term_tuple[2])
            # Otherwise, write the current lowest term to disk, and start processing the next term
            else:
                if last_min_term is not None:
                    # Write current term to file
                    outfile.write(str(last_min_term) + "\n")
                last_min_term = min_term_tuple
            # Add next term in the ordered array of terms to the priority queue
            i = min_term_tuple[1]
            # Note that the file pointer always goes down in each file, so we can just read the next line
            line = block_files[i].readline().strip()
            if line != "":
                next_min_term_tuple = literal_eval(line)
                min_heap.push((next_min_term_tuple[0], i, next_min_term_tuple[1]))
            # Write the final term
            if min_heap.empty():
                outfile.write(str(last_min_term))
        # Close all block files
        for i in range(k):
            block_files[i].close()


    """ Expected results---
    Primary memory (dictionary):
    {
    brutus:[(1,5),(2,7)],
    light:[(1,5),(2,5)]
    }
    File (blockX.txt): X e Z+
    ("brutus",[(1,5),(2,7)])
    ("light",[(1,5),(2,5)])
    """

    # Single-pass in-memory indexing algorithm
    def SPIMI_INVERT(self, number_block: int, token_stream_file) -> None:
        # New output file
        output_file = open(f"back\\block{number_block}.txt",mode="w")
        # New hash
        dictionary = {}
        while (len(dictionary) < MAX_TERM_AVAILABLE):
            term = token_stream_file.readline()[:-1]
            if not term:
                break
            term = literal_eval(term)
            if term[0] not in dictionary:
                dictionary[term[0]] = [(term[1],term[2])]
            else:
                dictionary[term[0]].append((term[1],term[2]))
            # Line 8 and 9 from pseudocode are skipped because dictionaries in Python are dynamic.  
        # Line 11 from pseudocode is skipped because in the preproccesing token_stream.txt is already sorted.
        dictionary = dict(sorted(dictionary.items(), key= lambda x: x[0], reverse=False)) # changes block
        # This logic is necessary to avoid writing a skip line at the eof
        for term_key in dictionary:
            if term_key == list(dictionary)[-1]:
                output_file.write(f"('{term_key}',{dictionary[term_key]})")
            else:
                output_file.write(f"('{term_key}',{dictionary[term_key]})\n")
        # Line 13 skipped from pseudocode, no need to return the file (?) as it is writted lol. But we can close it as a good student :)
        output_file.close()


    """
        Build the inverted index file with the collection using
        Single Pass In-Memory Indexing
    """
    def SPIMIIndexConstruction(self):
        # Define id for block
        n = 0
        # Ask user if is necessary to preprocess
        if input("Would you like to preprocess (Y/N)?: ").strip() == 'Y':
            if input("Are you sure (Y/N)?: ").strip() == 'Y':
                token_stream = self._preprocess()
            else:
                token_stream = "back\\token_stream.txt"
        else:
            token_stream = "back\\token_stream.txt"
        # Open the token_stream_file where we are going to construct our index
        token_stream_file = open(token_stream,mode="r")
        # Define some variables to determinate if the actual file is at eof
        last_pos = token_stream_file.tell()
        line = token_stream_file.readline()
        # Declare a list where will be block name as merge_blocks() function requires it
        blocks = []
        while line != '':
            token_stream_file.seek(last_pos)
            # Change block id
            n += 1
            blocks.append(f"back\\block{n}.txt")
            self.SPIMI_INVERT(n,token_stream_file)
            # Redefine variables to determinate if the actual file is at eof
            last_pos = token_stream_file.tell()
            line = token_stream_file.readline()
        # Proceed to merge all blocks in the list
        self.merge_blocks(blocks)



def main():
    
    mindicio = InvertedIndex("xednIdetrevnI")
    mindicio.SPIMIIndexConstruction()


if __name__ == "__main__":
    main()

