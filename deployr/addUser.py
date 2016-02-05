'''
1. Find the database credentials
2. Use pymongo to connect to database
3. Create new users if not exist
'''

import re

# Open the configuration file
file_name = '/home/miracle/deployr/7.4.1/deployr/deployr.groovy'
info = {}
# Read database credentials
with open(file_name, 'r') as f:
    for line in f.readlines():
        result = re.search('(\w+) = \"?([a-z\d\-]+)\"?', line)
        if result:
            info[result.group(1)] = result.group(2)

import os

deployr_user = os.environ['DEPLOYR_USER']
deployr_pass = 'changeme_deployr'
deployr_pass_admin = 'changeme_deployr_admin'

import uuid, bcrypt
from pymongo import MongoClient
from datetime import datetime

# Connect to mongoDB (at port 7403 of the deployr server by default)
client = MongoClient('mongodb://%s:%s@%s:%s/' % (info['username'], info['password'], info['host'], info['port']))
db = client[info['databaseName']]

# Get the ids for different user roles
role = db.role
id_power_user = role.find_one({'authority':'ROLE_POWER_USER'})['_id']
id_package_manager = role.find_one({'authority':'ROLE_PACKAGE_MANAGER'})['_id']
id_basic_user = role.find_one({'authority':'ROLE_BASIC_USER'})['_id']

# Get the collections
user = db.user
user_role = db.userRole
user_role_next_id = db.userRole.next_id

# Create a new user (specify username, password, and displayName)
new_user = {
    "_id" : "USER-" + str(uuid.uuid4()),
    "accountExpired" : False,
    "accountLocked" : False,
    "accountTally" : 0,
    "accountTallyStamp" : 0L,
    "dateCreated" : datetime.utcnow(),
    "displayName" : "Miracle DeployR User",
    "enabled" : True,
    "lastUpdated" : datetime.utcnow(),
    "password" : bcrypt.hashpw(deployr_pass, bcrypt.gensalt(14, '2a')),
    "passwordExpired" : False,
    "username" : deployr_user,
    "version" : 0L
}
# Find the userRole max id
new_user_role_next_id = user_role_next_id.find_one({})['next_id']
# Create new user role data
new_user_role = [
    {
        "_id" : long(new_user_role_next_id + 1),
        "role" : id_basic_user,
        "user" : new_user['_id']
    },
    {
        "_id" : long(new_user_role_next_id + 2),
        "role" : id_package_manager,
        "user" : new_user['_id']
    }
]

# Check if deployr_user already exist
if user.find({"username": deployr_user}).count() == 0:
    # Insert new user
    user.insert_one(new_user)
    # Insert role memberhship
    user_role.insert_many(new_user_role)
    # Update user_role_next_id
    user_role_next_id.update_one({'_id': 'userRole'}, {'$set': {'next_id': new_user_role_next_id + 2}})
else:
    print("User already exist")

# Update password for the admin user
user.update_one(
    {"username": "admin"},
    {
        "$set": {
            "password": bcrypt.hashpw(deployr_pass_admin, bcrypt.gensalt(14, '2a')),
            "passwordExpired": False
        },
        "$currentDate": {"lastUpdated": True}
    }
)    

# Remove testuser
user.delete_one({"username": "testuser"})

# Disconnect
client.close()
