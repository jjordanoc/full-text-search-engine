import json
import math
import os
import struct
import timeit
from ast import literal_eval
from typing import List, TextIO, Tuple, Optional, Dict, BinaryIO

from nltk.stem.snowball import SnowballStemmer
from nltk.tokenize import RegexpTokenizer

from Heap import MinHeap


def measure_execution_time(func):
    def wrapper(*args, **kwargs):
        start_time = timeit.default_timer()
        result = func(*args, **kwargs)
        end_time = timeit.default_timer()
        execution_time = end_time - start_time
        print(f"Execution time of {func.__name__}: {execution_time} seconds")
        return result

    return wrapper


struct_ftm_float = 'f'
struct_len_float = struct.calcsize(struct_ftm_float)
struct_unpack_float = struct.Struct(struct_ftm_float).unpack_from

struct_fmt_int = 'I'
struct_len_int = struct.calcsize(struct_fmt_int)
struct_unpack_int = struct.Struct(struct_fmt_int).unpack_from


class InvertedIndex:

    def __init__(self, raw_data_file_name: str, stoplist_file_name: str = "", index_name: str = "myindex"):
        self.raw_data_file_name = raw_data_file_name
        index_name = "index/" + index_name
        # File that maps document ids to actual documents
        self.doc_map_file_name = index_name + "_docmap.invidx"
        # File that stores the terms and their posting lists
        self.index_file_name = index_name + "_index.invidx"
        # File that stores the norm of the tf_idf vectors of each document
        self.length_file_name = index_name + "_length.invidx"
        # File that stores the number of documents
        self.n_file_name = index_name + "_n.invidx"
        # File that stores the number of terms in the inverted index
        self.total_terms_file_name = index_name + "_total_terms.invidx"
        # File that maps the logical position of each term in the inverted index to its physical position
        self.header_terms_file_name = index_name + "_header_terms.invidx"

        # Temporary file that collects tokens
        self.token_stream_file_name = index_name + "token_stream.invidxtmp"
        # Temporary file that stores each block to merge during SPIMI Invert
        self.block_file_name = lambda block_number: f"{index_name}_block{block_number}.invidxtmp"

        # Other constants
        self.spimi_max_terms_per_hash = 200000
        # Stemmer for reducing english words into their word stem
        self.stemmer = SnowballStemmer('english')
        # Filter to just accept words with normal letter, capital letter and also tildes
        self.tokenizer = RegexpTokenizer(r'[a-zA-ZÀ-ÿ]+')
        # Stowords
        self.stopwords = None
        if stoplist_file_name != "":
            with open(stoplist_file_name) as stoplist:
                lower_stopword_list = [tk.lower() for tk in self.tokenizer.tokenize(stoplist.read())]
                self.stopwords = set(lower_stopword_list)

        # Load number of documents
        if os.path.exists(self.n_file_name):
            with open(self.n_file_name, mode="r") as n_file:
                self.n = int(n_file.readline())
        else:
            self.n = 0

        # Load number of terms
        if os.path.exists(self.total_terms_file_name):
            with open(self.total_terms_file_name, mode="r") as total_terms_file:
                self.total_terms = int(total_terms_file.readline())
        else:
            self.total_terms = 0

    """
        Preprocess all documents, and create a temporary
        file containing the following information:
        (term, doc_id, term_frequency) #doc_id: posicion logica
    """

    def _preprocess(self, texto: str) -> Dict[str, int]:
        # tokenizar
        lower_token_list = [tk.lower() for tk in self.tokenizer.tokenize(texto)]
        # filtrar stopwords y contar
        tokens_count = dict()
        for tk in lower_token_list:
            if tk not in self.stopwords:
                if tk in tokens_count:
                    tokens_count[tk] += 1
                else:
                    tokens_count[tk] = 1
        # reducir palabras y agrupar
        stemmed_tokens_count = dict()
        for tk in tokens_count:
            stemmed = self.stemmer.stem(tk)
            if stemmed in stemmed_tokens_count:
                stemmed_tokens_count[stemmed] += tokens_count[tk]
            else:
                stemmed_tokens_count[stemmed] = tokens_count[tk]
        return stemmed_tokens_count

    def _preprocess_documents(self) -> None:
        with open(self.raw_data_file_name) as file, open(self.doc_map_file_name, mode="w") as header_file, open(
                self.token_stream_file_name, mode="w") as token_stream_file:
            logic_pos = 1
            longitud = 0
            while True:
                line = file.readline().strip()
                if not line:
                    break
                posicion_logica = str(logic_pos).ljust(8)
                posicion_fisica = str(longitud)
                header_file.write(f"{posicion_logica}{posicion_fisica}\n")
                longitud += len(line)
                line = json.loads(line)
                documento_procesado = self._preprocess(line["abstract"])
                documento_procesado = dict(sorted(documento_procesado.items(), key=lambda x: x[0], reverse=False))
                for key in documento_procesado:
                    token_stream_file.write(f"('{key}',{logic_pos},{documento_procesado[key]})\n")
                logic_pos += 1
                self.n += 1
        # Name's file where is the information as (term, doc_id, term_frequency)
        with open(self.n_file_name, mode="w") as n_file:
            n_file.write(str(self.n))

    @measure_execution_time
    def _merge_blocks(self, blocks: List[str]) -> None:
        outfile = open(self.index_file_name, "w")
        header = open(self.header_terms_file_name, "wb")
        length_file = open(self.length_file_name, "wb+")
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
        term_num = 1
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
                    posting_list: List[Tuple[int, int]] = last_min_term[2]
                    term = (last_min_term[0], posting_list, term_num)
                    term_num += 1
                    df_t = len(posting_list)
                    # seek length file for each doc
                    # add product of tf * idf squared
                    # sqrt (at the end)
                    for d, tf_t_d in posting_list:
                        length_file.seek((d - 1) * struct_len_float)
                        line = length_file.read(struct_len_float)
                        if line:
                            val = struct_unpack_float(line)[0]
                        else:
                            val = 0
                        val += (math.log10(1 + tf_t_d) * math.log10(self.n / df_t)) ** 2
                        s = struct.pack('f', val)
                        length_file.seek((d - 1) * struct_len_float)
                        length_file.write(s)
                    pos = outfile.tell()
                    pos = struct.pack('I', pos)
                    header.write(pos)
                    outfile.write(str(term) + "\n")
                    self.total_terms += 1
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
                # Write current term to file
                posting_list: List[Tuple[int, int]] = last_min_term[2]
                term = (last_min_term[0], posting_list)
                df_t = len(posting_list)
                # seek length file for each doc
                # add product of tf * idf squared
                # sqrt (at the end)
                for d, tf_t_d in posting_list:
                    length_file.seek((d - 1) * struct_len_float)
                    line = length_file.read(struct_len_float)
                    if line:
                        val = struct_unpack_float(line)[0]
                    else:
                        val = 0
                    val += (tf_t_d * math.log10(self.n / df_t)) ** 2
                    s = struct.pack('f', val)
                    length_file.seek((d - 1) * struct_len_float)
                    length_file.write(s)
                pos = outfile.tell()
                pos = struct.pack('I', pos)
                header.write(pos)
                outfile.write(str(term))
                self.total_terms += 1
        with open(self.total_terms_file_name, mode="w") as total_terms_file:
            total_terms_file.write(str(self.total_terms))
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
    def _spimi_invert(self, block_number: int, token_stream_file) -> None:
        # New output file
        output_file = open(self.block_file_name(block_number), mode="w")
        # New hash
        dictionary = {}
        while len(dictionary) < self.spimi_max_terms_per_hash:
            term = token_stream_file.readline()[:-1]
            if not term:
                break
            term = literal_eval(term)
            if term[0] not in dictionary:
                dictionary[term[0]] = [(term[1], term[2])]
            else:
                dictionary[term[0]].append((term[1], term[2]))
            # Line 8 and 9 from pseudocode are skipped because dictionaries in Python are dynamic.
        # Line 11 from pseudocode is skipped because in the preproccesing token_stream.txt is already sorted.
        dictionary = dict(sorted(dictionary.items(), key=lambda x: x[0], reverse=False))  # changes block
        # This logic is necessary to avoid writing a skip line at the eof
        for term_key in dictionary:
            if term_key == list(dictionary)[-1]:
                output_file.write(f"('{term_key}',{dictionary[term_key]})")
            else:
                output_file.write(f"('{term_key}',{dictionary[term_key]})\n")
        # Line 13 skipped from pseudocode, no need to return the file (?) as it is writted lol. But we can close it
        # as a good student :)
        output_file.close()

    """
        Build the inverted index file with the collection using
        Single Pass In-Memory Indexing
    """

    @measure_execution_time
    def _spimi_index_construction(self) -> None:
        # Define id for block
        n = 0
        # Ask user if is necessary to preprocess
        self._preprocess_documents()
        # Open the token_stream_file where we are going to construct our index
        with open(self.token_stream_file_name, mode="r") as token_stream_file:
            # Define some variables to determinate if the actual file is at eof
            last_pos = token_stream_file.tell()
            line = token_stream_file.readline().strip()
            # Declare a list where will be block name as merge_blocks() function requires it
            blocks = []
            while line != '':
                token_stream_file.seek(last_pos)
                # Change block id
                n += 1
                blocks.append(self.block_file_name(n))
                self._spimi_invert(n, token_stream_file)
                # Redefine variables to determinate if the actual file is at eof
                last_pos = token_stream_file.tell()
                line = token_stream_file.readline().strip()
            # Proceed to merge all blocks in the list
            self._merge_blocks(blocks)

    def create(self):
        self.n = 0
        self.total_terms = 0
        self._spimi_index_construction()
        # self._obtain_lengths()

    def _binary_search_term_aux(self, header_term_file: BinaryIO, index_file: TextIO, term: str, start: int,
                                end: int) -> Optional[List[Tuple[int, int]]]:
        if start > end:
            return None
        mid = math.floor((end + start) / 2)
        header_term_file.seek(mid * 4)
        header_file_line = header_term_file.read(struct_len_int)
        physical_pos = int(struct_unpack_int(header_file_line)[0])
        index_file.seek(physical_pos)
        line: str = index_file.readline()
        item: Tuple = literal_eval(line)
        current_term: str = item[0]
        if term == current_term:
            return item[1]
        elif term > current_term:
            return self._binary_search_term_aux(header_term_file, index_file, term, mid + 1, end)
        else:
            return self._binary_search_term_aux(header_term_file, index_file, term, start, mid - 1)

    def _binary_search_term(self, header_term_file: BinaryIO, index_file: TextIO, term: str) -> Optional[
        List[Tuple[int, int]]]:
        return self._binary_search_term_aux(header_term_file, index_file, term, 0, self.total_terms)

    @measure_execution_time
    def _obtain_lenghts_binary(self, lenght_file: str):
        lengths: Dict[int, float] = {}
        with open(lenght_file, mode="rb") as length_file:
            doc = 0
            while True:
                line = length_file.read(struct_len_float)
                if not line:
                    break
                doc += 1
                # These values are raw (no sqrt)
                lengths[doc] = math.sqrt(struct_unpack_float(line)[0])
        return lengths

    @measure_execution_time
    def cosine_score(self, query: str, k: int):
        lengths: Dict[int, float] = self._obtain_lenghts_binary(self.length_file_name)

        with open(self.index_file_name) as index_file, open(self.header_terms_file_name,
                                                            mode="rb") as header_terms_file:
            query_processed = self._preprocess(query)
            scores: Dict[int, float] = {}
            norm_q = 0
            query_processed = dict(sorted(query_processed.items(), key=lambda x: x[0], reverse=False))
            for query_term in query_processed:
                tf_term_q: int = query_processed[query_term]
                postings_list_term = self._binary_search_term(header_terms_file, index_file, query_term)
                df_term = len(postings_list_term)
                tf_idf_t_q = math.log10(1 + tf_term_q) * math.log10(self.n / df_term)
                norm_q += tf_idf_t_q ** 2
                for d, tf_term_d in postings_list_term:
                    tf_idf_t_d = math.log10(1 + tf_term_d) * math.log10(self.n / df_term)
                    if d in scores:
                        scores[d] += tf_idf_t_d * tf_idf_t_q
                    else:
                        scores.update({d: tf_idf_t_d * tf_idf_t_q})
            norm_q = math.sqrt(norm_q)
            for d in scores:
                scores[d] = scores[d] / (lengths[d] * norm_q)
            return list(sorted(scores.items(), key=lambda x: x[1], reverse=True))[0:k + 1]


def main():
    index = InvertedIndex(raw_data_file_name="test.json",
                          index_name="inverted_index",
                          stoplist_file_name="stoplist.txt")

    query = "  A fully differential calculation in perturbative quantum chromodynamics is\npresented for the production of massive photon pairs at hadron colliders. All\nnext-to-leading order perturbative contributions from quark-antiquark,\ngluon-(anti)quark, and gluon-gluon subprocesses are included, as well as\nall-orders resummation of initial-state gluon radiation valid at\nnext-to-next-to-leading logarithmic accuracy. The region of phase space is\nspecified in which the calculation is most reliable. Good agreement is\ndemonstrated with data from the Fermilab Tevatron, and predictions are made for\nmore detailed tests with CDF and DO data. Predictions are shown for\ndistributions of diphoton pairs produced at the energy of the Large Hadron\nCollider (LHC). Distributions of the diphoton pairs from the decay of a Higgs\nboson are contrasted with those produced from QCD processes at the LHC, showing\nthat enhanced sensitivity to the signal can be obtained with judicious\nselection of events.\n"
    topk = index.cosine_score(query, 5)
    print(topk)


if __name__ == "__main__":
    main()
