import pymongo
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path='backend/.env')

def test_mongodb_connection():
    """
    Tests the MongoDB connection using the URI from the .env file.
    """
    mongodb_uri = os.getenv("MONGODB_URI")
    if not mongodb_uri:
        print("MONGODB_URI not found in .env file.")
        return

    try:
        client = pymongo.MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
        client.server_info()  # Force connection on a request as the connect=True parameter of MongoClient seems to be deprecated
        print("MongoDB connection successful.")
    except pymongo.errors.ConnectionFailure as e:
        print(f"MongoDB connection failed: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    test_mongodb_connection()