"""
Database initialization and configuration for MongoDB Atlas
This module handles the PyMongo setup and provides access to database collections
"""

import os
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# Global MongoDB instance
mongo = None

def init_mongo(app):
    """
    Initialize MongoDB connection with the Flask app
    
    Args:
        app: Flask application instance
        
    Returns:
        PyMongo instance
    """
    global mongo
    
    # Configure MongoDB URI
    app.config['MONGO_URI'] = os.getenv('MONGO_URI')
    
    if not app.config['MONGO_URI']:
        raise ValueError("MONGO_URI environment variable is not set")
    
    # Initialize PyMongo
    mongo = PyMongo(app)
    
    # Test connection
    try:
        mongo.db.command('ping')
        print("✅ MongoDB connection established successfully")
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        raise
    
    return mongo

def get_mongo():
    """
    Get the MongoDB instance
    
    Returns:
        PyMongo instance
    """
    return mongo

def get_collection(collection_name):
    """
    Get a specific MongoDB collection
    
    Args:
        collection_name: Name of the collection
        
    Returns:
        MongoDB collection
    """
    if not mongo:
        raise RuntimeError("MongoDB not initialized. Call init_mongo() first.")
    
    return mongo.db[collection_name]

# Helper functions for ObjectId
def create_object_id():
    """Create a new ObjectId"""
    return ObjectId()

def is_valid_object_id(id_string):
    """Check if a string is a valid ObjectId"""
    try:
        ObjectId(id_string)
        return True
    except:
        return False

def string_to_object_id(id_string):
    """Convert string to ObjectId"""
    try:
        return ObjectId(id_string)
    except:
        raise ValueError(f"Invalid ObjectId: {id_string}")
