from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table, Column, Integer,Date, String,Float, MetaData, ForeignKey
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

#SQLAlchemy
engine = create_engine('sqlite:///wdqs.db', echo=True)
Base = declarative_base()

Session = scoped_session(sessionmaker(bind=engine))

class DefaultRecord(Base):
    __tablename__ = 'default_records'
    prj_id = Column(Integer,primary_key = True)
    date = Column(Date,primary_key = True)
    month = Column(String,primary_key = True)
    prj_name = Column(String)
    type = Column(String,primary_key = True)
    amount = Column(Float)
#Base.metadata.drop_all(engine)
Base.metadata.create_all(engine)

def save_credit_assign():
    pass

def del_default_record(month):
    session = Session()
    try:
        session.query(DefaultRecord) \
               .filter(DefaultRecord.month == month) \
               .delete()
        session.commit()
    except Exception, ex:
        session.rollback()
        raise ex

def save_default_record(lsr):
    session = Session()
    
    try:
        ls_obj = [DefaultRecord(**r) for r in lsr]
        session.bulk_save_objects(ls_obj)
        session.commit()
    except Exception, ex:
        session.rollback()
        raise ex

