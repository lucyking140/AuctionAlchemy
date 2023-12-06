from os import environ

DB_URI = environ.get('AA_DB_URI')
DEBUG = environ.get('AA_FLASK_DEBUG')