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
from typing import List, TextIO, Tuple, Optional, Dict
from Heap import MinHeap
import math
import timeit
import struct
from objsize import get_deep_size
# Unused
PAGE_SIZE = 128000000 #128MB
# Used in SPIMI
MAX_TERM_AVAILABLE = 1000 #1000000

# Stemmer for reducing english words into their word stem
stemmer = SnowballStemmer('english')
# Filter to just accept words with normal letter, capital letter and also tildes
tokenizer = RegexpTokenizer(r'[a-zA-ZÀ-ÿ]+')

stopwords = open("back\stoplist.txt","r",encoding="utf-8")
lower_stopword_list = [tk.lower() for tk in tokenizer.tokenize(stopwords.read())]
stopwords = set(lower_stopword_list)






class InvertedIndex:

    def __init__(self, collection_path: str, filename: str = "myindex"):
        self.doc_map_file_name = filename + "_docmap.invidx"
        self.index_file_name = filename + "_index.invidx"
        self.length_file_name = filename + "_length.invidx"
        self.collection_path = collection_path
        self.n_file_name = filename + "_n.invidx"
        self.header_terms_file_name = filename + "_header_terms.invidx"
        if os.path.exists(self.n_file_name):
           with open(self.n_file_name, mode = "r") as n_file:
            self.n = int(n_file.readline())
        else:
            self.n = 0

    """
        Preprocess all documents, and create a temporary
        file containing the following information:
        (term, doc_id, term_frequency) #doc_id: posicion logica
    """

    def _preprocess(self, texto: str) -> Dict[str,int]:
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
    
    def _preprocess_documents(self):
        # Set n to 0
        self.n = 0
        with open("back\\test.json") as file:
            header_file = open("back\header.txt",mode="w")
            token_stream_file = open("back\\token_stream.txt",mode="w")
            logic_pos = 1
            longitud = 0
            while True:
                line = file.readline().strip()
                if not line:
                    header_file.close()
                    token_stream_file.close()
                    break
                posicion_logica = str(logic_pos).ljust(8)    
                posicion_fisica = str(longitud)           
                header_file.write(f"{posicion_logica}{posicion_fisica}\n")
                longitud += len(line)
                line = json.loads(line)
                documento_procesado = self._preprocess(line["abstract"])
                documento_procesado = dict(sorted(documento_procesado.items(), key=lambda x: x[0],reverse=False))
                for key in documento_procesado:
                    token_stream_file.write(f"('{key}',{logic_pos},{documento_procesado[key]})\n")
                logic_pos += 1
                self.n += 1
        # Name's file where is the information as (term, doc_id, term_frequency)
        with open(self.n_file_name, mode = "w") as n_file:
            n_file.write(str(self.n))
        return "back\\token_stream.txt"

    def _merge_blocks(self, blocks: List[str]) -> None:
        outfile = open(self.index_file_name, "w")
        header = open(self.header_terms_file_name, "w")
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
                    term = (last_min_term[0],last_min_term[2])
                    pos = outfile.tell()
                    header.write(str(pos) + "\n")
                    outfile.write(str(term) + "\n")
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
                term = (last_min_term[0],last_min_term[2]) 
                pos = outfile.tell()
                header.write(str(pos))
                outfile.write(str(term))
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
    def _spimi_invert(self, number_block: int, token_stream_file) -> None:
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


    def _obtain_lengths(self) -> None:
        if input("Would you like to obtain lengths (Y/N)? ").strip().lower() == 'n':
            if input("Are you sure (Y/N)? ").strip().lower() == 'y':
                return 0
        with open("back\\token_stream.txt", mode="r") as token_stream, open(self.length_file_name, mode="w") as length_file, open(self.index_file_name, mode="r") as index_file:
                last_doc_id = 1
                cum: float = 0
                while True:
                    line: str = token_stream.readline().strip()
                    if not line:
                        break
                    token: Tuple[str, int, int] = literal_eval(line)
                    term: str = token[0]
                    doc_id: int = token[1]
                    tf: int = token[2]
                    if doc_id != last_doc_id:
                        last_doc_id = doc_id
                        length_file.write(str(math.sqrt(cum)) + "\n")
                        cum = 0
                    df_term = len(self._sequencial_search_term(index_file, term))
                    cum += (math.log10(1+tf) * math.log10(self.n/df_term)) ** 2
                length_file.write(str(math.sqrt(cum)))
                
    """
        Build the inverted index file with the collection using
        Single Pass In-Memory Indexing
    """
    def _spimi_index_construction(self):
        if input("Would you like to construct index (Y/N)? ").strip().lower() == 'n':
            if input("Are you sure (Y/N)? ").strip().lower() == 'y':
                return 0
        # Define id for block
        n = 0
        # Ask user if is necessary to preprocess
        token_stream = self._preprocess_documents()
        # Open the token_stream_file where we are going to construct our index
        token_stream_file = open(token_stream,mode="r")
        # Define some variables to determinate if the actual file is at eof
        last_pos = token_stream_file.tell()
        line = token_stream_file.readline().strip()
        # Declare a list where will be block name as merge_blocks() function requires it
        blocks = []
        while line != '':
            token_stream_file.seek(last_pos)
            # Change block id
            n += 1
            blocks.append(f"back\\block{n}.txt")
            self._spimi_invert(n,token_stream_file)
            # Redefine variables to determinate if the actual file is at eof
            last_pos = token_stream_file.tell()
            line = token_stream_file.readline().strip()
        # Proceed to merge all blocks in the list
        self._merge_blocks(blocks)
    
    def create(self):
        self._spimi_index_construction()
        self._obtain_lengths()
        
    def _sequencial_search_term(self, index_file: TextIO, term: str) -> Optional[List[Tuple[int, int]]]:
        index_file.seek(0)
        while True:
            line: str = index_file.readline().strip()
            if not line:
                break
            item: Tuple = literal_eval(line)
            current_term: str = item[0] 
            postings_list: List[Tuple[int, int]] = item[1]
            if current_term == term:
                return postings_list
        return None
        
    def _binary_search_term_aux(self, index_file: TextIO, term: str, start: int, end: int) -> Optional[List[Tuple[int, int]]]:
        if start > end:
            return None
        mid = math.floor((end + start) / 2)
        index_file.seek(mid)
        line: str = index_file.readline()
        item: Tuple = literal_eval(line)
        current_term: str = item[0]
        if term == current_term:
            return item[1]
        elif term > current_term:
            return self._binary_search_term(index_file, term, mid+1, end)
        else:
            return self._binary_search_term(index_file, term, start, mid)
        
    def _binary_search_term(self, index_file: TextIO, term: str) -> Optional[List[Tuple[int, int]]]:
        return self._binary_search_term_aux(index_file, term, 0, self.n)
    

    def _cosine_score(self, query: str, k: int):
        lengths: Dict[int, float] = {}
        with open(self.length_file_name, mode="r") as file:
            doc = 0
            while True:
                line = file.readline().strip()
                if not line:
                    break
                doc += 1
                lengths[doc] = float(line)
                
        with open(self.index_file_name) as index:
            query_processed = self._preprocess(query)
            scores: Dict[int, float] = {}
            norm_q = 0
            for query_term in query_processed:
                tf_term_q: int = query_processed[query_term]
                postings_list_term = self._sequencial_search_term(index, query_term)
                df_term = len(postings_list_term)
                tf_idf_t_q = math.log10(1+tf_term_q) * math.log10(self.n/df_term)
                norm_q += tf_idf_t_q ** 2
                for d, tf_term_d in postings_list_term:
                    tf_idf_t_d = math.log10(1+tf_term_d) * math.log10(self.n/df_term)
                    if d in scores:
                        scores[d] += tf_idf_t_d * tf_idf_t_q
                    else:
                        scores.update({d: tf_idf_t_d * tf_idf_t_q})
            norm_q = math.sqrt(norm_q)
            for d in scores:
                scores[d] = scores[d] / (lengths[d] * norm_q)
            return list(sorted(scores.items(), key=lambda x: x[1], reverse=True))[:k+1]
        

def main():
    mindicio = InvertedIndex("xednIdetrevnI")
    mindicio.create()
    query = "  We give a prescription for how to compute the Callias index, using as\nregulator an exponential function. We find agreement with old results in all\nodd dimensions. We show that the problem of computing the dimension of the\nmoduli space of self-dual strings can be formulated as an index problem in\neven-dimensional (loop-)space. We think that the regulator used in this Letter\ncan be applied to this index problem.\n"
    #query = " Text about a new formulation about new material cores new formulation new material new material new material"
    start_time = timeit.default_timer()
    topk = mindicio._cosine_score(query,5)
    end_time = timeit.default_timer()
    print(topk)
    print(end_time - start_time)


if __name__ == "__main__":
    main()

