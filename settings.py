from os import environ

DB_URL = environ.get('DB_URI')
DEBUG = environ.get('FLASK_DEBUG')