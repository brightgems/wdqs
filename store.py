# coding: utf-8

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Table,Unicode, Column,Boolean, Integer,Date, String,Float, MetaData, ForeignKey, DateTime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from datetime import date
from dateutil.parser import parse

#SQLAlchemy
engine = create_engine('sqlite:///wdqs.db', echo=True)
#engine = create_engine('mysql+pymysql://wdqsjob:123456@127.0.0.1:3306/wdqs?charset=utf8') #13.75.40.204
Base = declarative_base()

Session = scoped_session(sessionmaker(bind=engine))

class CreditProject(Base):
    __tablename__ = 'credit_projects'
    id = Column(Integer,autoincrement=True,primary_key = True)
    href = Column(String(255))
    title = Column(Unicode(255))
    hour = Column(Integer)
    amount = Column(Float)
    interest = Column(Float)
    date = Column(String(255))
    term_months = Column(Integer)

class DefaultRecord(Base):
    __tablename__ = 'default_records'
    prj_id = Column(Integer,primary_key = True)
    date = Column(Date,primary_key = True)
    month = Column(String(255),primary_key = True)
    prj_name = Column(String(255))
    type = Column(String(255),primary_key = True)
    amount = Column(Float)

class OwnedCredit(Base):
    __tablename__ = 'owned_credits'
    id = Column(Integer, primary_key=True)
    projectID = Column(Integer)
    contractID = Column(String(255))
    projectCategory = Column(String(255))
    projectRate = Column(Float)
    financingMaturity = Column(Float)
    repaymentCalcType = Column(String(255))
    cardNo = Column(String(255))
    repaymentDesc = Column(String(255))
    investmentID = Column(String(255))
    date = Column(Date,default = date.today())
    dealDate = Column(String(255))
    projectRepaymentDate = Column(String(255))
    remainMaturityDays = Column(Integer)
    canCreditAssign = Column(Boolean)
    holdAmount = Column(Float)
    fairAmount = Column(Float)

class ProjectDetails(Base):
    __tablename__ = 'project_details'

    projectID = Column(Integer, primary_key=True)
    projectName = Column(String(255, convert_unicode=True))
    userName = Column(String(255))
    borrowerName = Column(String(255))
    borrowerType = Column(String(255)) # 主体性质: 法人/个人
    borrowerGender = Column(String(255))
    borrowerAge = Column(String(255))
    workCity = Column(String(255))
    cardNum = Column(String(255))
    education = Column(String(255))
    marriageStatus = Column(String(255))
    loanApplyCity = Column(String(255))
    incomeRange = Column(String(255))
    employerType = Column(String(255))
    # loanInfo
    repaymentMethod = Column(String(255))
    loanAmount = Column(Integer)
    loanMonth = Column(Integer) # month
    overdueCount = Column(Integer)
    currentOverdueAmount = Column(Float)
    historyOverdueAmount = Column(Float)
    loanStDt = Column(DateTime)


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
    except Exception as ex:
        session.rollback()
        raise ex

def save_default_record(lsr):
    session = Session()
    
    try:
        ls_obj = [DefaultRecord(**r) for r in lsr]
        session.bulk_save_objects(ls_obj)
        session.commit()
    except Exception as ex:
        session.rollback()
        raise ex

def save_owned_credits(lsoc):
    session = Session()
    try:
        session.query(OwnedCredit).delete()
        session.commit()
        lsoc_new = []
        for r in lsoc:
            rnew = dict([r for r in r.items() if hasattr(OwnedCredit,r[0])])
            lsoc_new.append(rnew)
        ls_obj = [OwnedCredit(**r) for r in lsoc_new]
        
        session.bulk_save_objects(ls_obj)
        session.commit()
    except Exception as ex:
        print(ex)
        session.rollback()
        raise ex

def save_credit_projects(lsp):
    session = Session()
    dates = set()
    
    [dates.add(x['date']) for x in lsp]
    try:
        session.query(CreditProject) \
            .filter(CreditProject.date.in_(dates)) \
            .delete(synchronize_session=False)
        session.commit()
        lsoc_new = []
        for r in lsp:
            rnew = dict([r for r in r.items() if hasattr(CreditProject,r[0])])
            lsoc_new.append(rnew)
        ls_obj = [CreditProject(**r) for r in lsoc_new]
        
        session.bulk_save_objects(ls_obj)
        session.commit()
    except Exception as ex:
        print(ex)
        session.rollback()
        raise ex


def save_project_details(lsp):
    session = Session()
    ls_prjid = set()
    
    [ls_prjid.add(int(x['projectID'])) for x in lsp]
    try:
        session.query(ProjectDetails) \
            .filter(ProjectDetails.projectID.in_(ls_prjid)) \
            .delete(synchronize_session=False)
            
        session.commit()
        print("deleted old prjs!")
        lsoc_new = []
        for r in lsp:
            rnew = dict([r for r in r.items() if hasattr(ProjectDetails,r[0])])
            lsoc_new.append(rnew)
        ls_obj = [ProjectDetails(**r) for r in lsoc_new]
        
        session.bulk_save_objects(ls_obj)
        session.commit()
    except Exception as ex:
        print(ex)
        session.rollback()
        raise ex