# db_connection.py

from pymongo import MongoClient
from collections import defaultdict

# Connect to MongoDB


def connectDataBase():
    DB_NAME = "CPP"
    DB_HOST = "localhost"
    DB_PORT = 27017

    try:
        client = MongoClient(host=DB_HOST, port=DB_PORT)
        db = client[DB_NAME]
        return db
    except:
        print("Database connection failed.")

# Function to create a new document


def createDocument(col, id, text, title, date, category):
    document = {
        "_id": id,
        "text": text,
        "title": title,
        "date": date,
        "category": category
    }
    try:
        col.insert_one(document)
        print(f"Document {id} created successfully.")
    except Exception as e:
        print(f"Error inserting document: {e}")

# Function to update an existing document


def updateDocument(col, id, text, title, date, category):
    updated_data = {
        "$set": {
            "text": text,
            "title": title,
            "date": date,
            "category": category
        }
    }
    result = col.update_one({"_id": id}, updated_data)
    if result.matched_count > 0:
        print(f"Document {id} updated successfully.")
    else:
        print(f"Document {id} not found.")

# Function to delete a document


def deleteDocument(col, id):
    result = col.delete_one({"_id": id})
    if result.deleted_count > 0:
        print(f"Document {id} deleted successfully.")
    else:
        print(f"Document {id} not found.")

# Function to output an inverted index


def getIndex(col):
    inverted_index = defaultdict(dict)

    for document in col.find():
        doc_title = document["title"]
        doc_text = document["text"]

        # Tokenizing the text by splitting on spaces
        terms = doc_text.split()

        # Building the inverted index
        for term in terms:
            if doc_title in inverted_index[term]:
                inverted_index[term][doc_title] += 1
            else:
                inverted_index[term][doc_title] = 1

    # Sorting the inverted index by term
    sorted_index = {}
    for term in sorted(inverted_index.keys()):
        doc_counts = ', '.join(
            [f"{doc}: {count}" for doc, count in sorted(inverted_index[term].items())])
        sorted_index[term] = doc_counts

    return sorted_index