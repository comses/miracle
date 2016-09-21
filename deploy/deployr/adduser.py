'''
This script has to access the deployr mongodb directly to add a user since the current version of DeployR does not have
a web API for creating a new user.

FIXME: eventually replace script with a Django management command, would need to expose the deployr.groovy file to
Django for mongodb access however.

1. Find the database credentials
2. Use pymongo to connect to database
3. Create new users if not exist
'''
import bcrypt
import logging
import os
import re
import uuid
import ConfigParser

from datetime import datetime
from pymongo import MongoClient

logger = logging.getLogger(__name__)

os.environ.setdefault('USERNAME', 'comses')
os.environ.setdefault('DEPLOYR_VERSION', '8.0.0')
os.environ.setdefault('DEPLOYR_USER', 'miracle')

COMSES_USERNAME = os.environ.get('USERNAME')
DEPLOYR_VERSION = os.environ.get('DEPLOYR_VERSION')

# Open the configuration file
deployr_groovy_file = '/home/{0}/deployr/{1}/deployr/deployr.groovy'.format(COMSES_USERNAME, DEPLOYR_VERSION)
mongodb = {}
# Read database credentials from groovy configuration file
with open(deployr_groovy_file, 'r') as f:
    for line in f.readlines():
        # captures all quoted strings of the form username="foo", assumes they are the db credentials.
        result = re.search(r'(\w+) = \"?([a-z\d\-]+)\"?', line)
        if result:
            mongodb[result.group(1)] = result.group(2)


config = ConfigParser.RawConfigParser({'user': os.environ.get('DEPLOYR_USER')})
config.read('/opt/deployr/deployr.conf')
deployr_user = config.get('deployr', 'user')
deployr_password = config.get('deployr', 'password')
deployr_admin_password = config.get('deployr', 'admin_password')

# Connect to mongoDB (at port 7403 of the deployr server by default)
client = MongoClient('mongodb://{0}:{1}@{2}:{3}/'.format(
    mongodb['username'], mongodb['password'], mongodb['host'], mongodb['port']))
db = client[mongodb['databaseName']]

# Get the ids for different user roles
role = db.role
id_power_user = role.find_one({'authority': 'ROLE_POWER_USER'})['_id']
id_package_manager = role.find_one(
    {'authority': 'ROLE_PACKAGE_MANAGER'})['_id']
id_basic_user = role.find_one({'authority': 'ROLE_BASIC_USER'})['_id']

# Get the collections
user = db.user
user_role = db.userRole
user_role_next_id = db.userRole.next_id

# Create a new user (specify username, password, and displayName)
new_user = {
    "_id": "USER-" + str(uuid.uuid4()),
    "accountExpired": False,
    "accountLocked": False,
    "accountTally": 0,
    "accountTallyStamp": 0,
    "dateCreated": datetime.utcnow(),
    "displayName": "Miracle DeployR User",
    "enabled": True,
    "lastUpdated": datetime.utcnow(),
    "password": bcrypt.hashpw(deployr_password, bcrypt.gensalt(14, '2a')),
    "passwordExpired": False,
    "username": deployr_user,
    "version": 0
}
# Find the userRole max id
new_user_role_next_id = user_role_next_id.find_one({})['next_id']
# Create new user role data
new_user_role = [
    {
        "_id": int(new_user_role_next_id + 1),
        "role": id_basic_user,
        "user": new_user['_id']
    },
    {
        "_id": int(new_user_role_next_id + 2),
        "role": id_package_manager,
        "user": new_user['_id']
    }
]

# Check if deployr_user already exist
if user.find({"username": deployr_user}).count() == 0:
    # Insert new user
    user.insert_one(new_user)
    # Insert role memberhship
    user_role.insert_many(new_user_role)
    # Update user_role_next_id
    user_role_next_id.update_one(
        {'_id': 'userRole'}, {'$set': {'next_id': new_user_role_next_id + 2}})
else:
    print("User already exist")

# Update password for the admin user
user.update_one(
    {"username": "admin"},
    {
        "$set": {
            "password": bcrypt.hashpw(deployr_admin_password, bcrypt.gensalt(14, '2a')),
            "passwordExpired": False
        },
        "$currentDate": {"lastUpdated": True}
    }
)

# Remove testuser if it exists
user.delete_one({"username": "testuser"})

# Disconnect
client.close()
