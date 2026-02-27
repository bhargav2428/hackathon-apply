"""
Database Configuration and Initialization - MongoDB
"""
import os
from flask_pymongo import PyMongo
from mongoengine import connect, disconnect

mongo = PyMongo()

def init_db(app):
    """Initialize MongoDB connection"""
    mongo_uri = os.environ.get('MONGO_URI', 'mongodb://localhost:27017/hackathon_agent')
    
    # Connect mongoengine
    connect(host=mongo_uri)
    
    # Initialize Flask-PyMongo
    app.config['MONGO_URI'] = mongo_uri
    mongo.init_app(app)
    
    print("MongoDB initialized successfully!")
    return mongo

def get_db():
    """Get MongoDB database instance"""
    return mongo.db
