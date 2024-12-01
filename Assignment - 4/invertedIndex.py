from pymongo import MongoClient
from nltk.tokenize import RegexpTokenizer
from sklearn.feature_extraction.text import TfidfVectorizer
from math import sqrt
from sklearn.metrics.pairwise import cosine_similarity


class DocumentSearchEngine():
    def __init__(self):
        # initialize MongoDB
        database = self.connect_to_db()
        self.inverted_index_collection = database['inverted_index']  # main collection
        self.document_collection = database['document_collection']  # to reference documents
        self.term_counter = 0
        self.doc_counter = 0
        # delete all documents currently in the collections
        self.inverted_index_collection.delete_many({})
        self.document_collection.delete_many({})
        # private variables
        self.tfidf_vectorizer = None
        self.document_vectors = []
        self.term_dictionary = {}

    def connect_to_db(self):
        DB_NAME = "CPP"
        DB_HOST = "localhost"
        DB_PORT = 27017
        try:
            client = MongoClient(host=DB_HOST, port=DB_PORT)
            database = client[DB_NAME]
            return database
        except:
            print("Failed to connect to database")

    def insert_document(self, doc_text):
        self.document_collection.insert_one(
            {"_id": self.doc_counter, "content": doc_text})
        self.doc_counter += 1

    def insert_term(self, term_id, doc_data):
        self.inverted_index_collection.insert_one(
            {"_id": self.term_counter, "term_id": term_id, "doc_data": doc_data})
        self.term_counter += 1

    def create_inverted_index(self):
        # retrieve documents from MongoDB
        docs_from_db = [doc['content'] for doc in self.document_collection.find()]
        # generate terms from documents
        self.tfidf_vectorizer = TfidfVectorizer(ngram_range=(1, 3))
        tfidf_matrix = self.tfidf_vectorizer.fit_transform(docs_from_db)
        # record vocabulary and document vectors
        self.term_dictionary = self.tfidf_vectorizer.vocabulary_  # just for debugging
        self.document_vectors = tfidf_matrix.toarray()
        # create inverted index
        term_doc_index = {}
        for doc_idx, term_idx in zip(*tfidf_matrix.nonzero()):
            tfidf_score = tfidf_matrix[doc_idx, term_idx]
            if term_idx not in term_doc_index:
                term_doc_index[term_idx] = {}
            term_doc_index[term_idx][str(doc_idx)] = tfidf_score
        # push to MongoDB
        for term_id, doc_mapping in term_doc_index.items():
            self.insert_term(int(term_id), doc_mapping)

    def rank_documents(self, search_query):
        # transform query using learned vocabulary and document frequencies
        query_vector = self.tfidf_vectorizer.transform([search_query]).toarray()[0]

        # calculate cosine similarity for each query/document pair
        similarity_scores = []
        for doc_id in range(self.doc_counter):
            similarity_score = round(cosine_similarity(
                [query_vector, self.document_vectors[doc_id]])[0][1], 2)
            similarity_scores.append((doc_id, similarity_score))

        # sort documents by similarity
        similarity_scores.sort(key=lambda x: x[1], reverse=True)
        for doc_id, score in similarity_scores:
            if score > 0:
                document = self.document_collection.find_one({"_id": doc_id})
                print(f"\"{document['content']}\", {score}")


if __name__ == '__main__':
    search_engine = DocumentSearchEngine()
    search_engine.insert_document(
        "After the medication, headache and nausea were reported by the patient.")
    search_engine.insert_document(
        "The patient reported nausea and dizziness caused by the medication.")
    search_engine.insert_document(
        "Headache and dizziness are common effects of this medication.")
    search_engine.insert_document(
        "The medication caused a headache and nausea, but no dizziness was reported.")
    search_engine.create_inverted_index()
    search_engine.rank_documents("nausea and dizziness")  # query 1
    print()
    search_engine.rank_documents("effects")              # query 2
    print()
    search_engine.rank_documents("nausea was reported")  # query 3
    print()
    search_engine.rank_documents("dizziness")            # query 4
    print()
    search_engine.rank_documents("the medication")       # query 5
