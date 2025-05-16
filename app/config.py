import os

basedir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(basedir, '../data/grylli.db')
SQLALCHEMY_DATABASE_URI = f"sqlite:///{db_path}"
