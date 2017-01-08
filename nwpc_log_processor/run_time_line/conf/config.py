from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# mysql sqlalchemy
SQLALCHEMY_DATABASE_URI = "mysql+mysqldb://" + \
                          "windroc" + \
                          ":" + "shenyang" + \
                          "@" + "192.168.2.10" + \
                          ":" + "3306" + \
                          "/" + "system-time-line" + \
                          "?" + "charset=utf8"

# mongodb
MONGODB_HOST = '192.168.2.10'
MONGODB_PORT = 27017

# mysql engine
engine = create_engine(SQLALCHEMY_DATABASE_URI)
Session = sessionmaker(bind=engine)
session = Session()


def create_mysql_engine():
    global engine, Session, session
    engine = create_engine(SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    session = Session()
