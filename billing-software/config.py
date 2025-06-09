from pymongo import MongoClient
from pymongo.server_api import ServerApi
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB Configuration
MONGO_URI ="mongodb+srv://kjsurendhar03:2002Kj@cluster0.txmk5.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
#Create a MongoClient instance
# Create a new client and connect to the server
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))

# Access the database and collections
db = client.ParkingTokenSystem
admins_collection = db.admins
users_collection = db.users
rates_collection = db.rates
vehicles_collection = db.vehicles
completed_records = db.completed_records
jobs_collection = db.jobs

# Application Configuration
SECRET_KEY = os.getenv('SECRET_KEY')
MASTER_KEY = os.getenv('MASTER_KEY')

# Global variables
default_user_setup_done = False 