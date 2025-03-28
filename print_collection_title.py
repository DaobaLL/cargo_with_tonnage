# Description: This script prints the title of each collection in the database and the columns in each collection.
# The script uses the pymongo library to connect to the MongoDB database and retrieve the collection names and column names.
from pymongo import MongoClient

def print_collection_titles():
    client = MongoClient('mongodb://localhost:27017/')
    db = client['cargo_with_tonnage']
    
    # Get all collection names
    collections = db.list_collection_names()
    
    # Print the title of each collection and its columns
    for collection in collections:
        print(f"Collection: {collection}")
        # Get the first document in the collection to retrieve the column names
        document = db[collection].find_one()
        if document:
            for column in document.keys():
                print(f" - Column: {column}")

# Call the function to print collection titles and columns
print_collection_titles()
