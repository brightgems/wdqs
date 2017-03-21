# coding:utf8
from store import save_default_record, del_default_record
import datetime


def test_save_default_record():
    
    d_= datetime.date.today()
    d_ = datetime.date(d_.year,d_.month,1)
    dtext = d_.strftime("%Y-%m-%d")
    lsr = [{'date':d_,'prj_id':3551662,'type':'i','prj_name':u'个人消费贷   5039294-1-1','amount':343}]
    save_default_record(lsr)
    del_default_record(d_)
    