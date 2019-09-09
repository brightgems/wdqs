# coding:utf8
from store import save_default_record, del_default_record,save_owned_credits
import datetime
import json

def test_save_default_record():
    
    d_= datetime.date.today()
    d_ = datetime.date(d_.year,d_.month,1)
    dtext = d_.strftime("%Y-%m-%d")
    lsr = [{'date':d_,'month':'201701','prj_id':3551662,'type':'i','prj_name':u'个人消费贷   5039294-1-1','amount':343}]
    save_default_record(lsr)
    del_default_record(d_)


def test_save_owned_credits():
    t = """[{ "projectID": 5030488, "contractID": "6733907-1-1", "projectCategory": "PersonalConsumer", "projectRate": 0.095000, "financingMaturity": 12.00, "repaymentCalcType": "EqualPrincipalAndInterest", "repaymentDesc": "等额本息", "investmentID": 21039055, "amount": 100.00, "factPayAmount": 100.00, "repaymentAmount": 16.01, "creditAssignedAmount": 0.00, "subscribeFinishAt": "2017-01-16 09:22:56", "projectRepaymentDate": "2018-01-15 22:00:00", "canCreditAssign": true, "dealDate": "2017-01-16 10:17:28", "projectInterestDaysType": "FixedDays30And360", "factProfit": 1.51, "creditAssignFactSoldAmount": 0, "bidCreditAssignAmount": 0, "investedCreditAssignAmount": 0, "investedCreditAssignSoldAmount": 0, "notRepayInterest": 3.71, "holdAmount": 83.99, "couponRate": 0, "remainMaturityDays": 287, "notRepaymentAmount": 87.70, "repayPrincipalAndInterest": 17.52, "fairAmount": 84.41, "serviceFee": 0, "receiptToNowAmount": 0, "receivableToNowInterest": 0.42, "investResultAmount": 1.93, "haveRepaidAmount": 17.52, "holdInvestmentDays": 77, "projectInterestAmount": 0, "projectAmount": 0, "creditAssignFinished": false, "havePaiedServiceFee": 0, "tips": "", "projectName": "个人消费贷 6733907-1-1", "ProjectDisplayName": "个人消费贷 6733907-1-1", "repaymentCalcTypeStr": "等额本息", "projectCategoryStr": "个人消费贷", "inProgressFlagStr": "" }]"""
    trs = json.loads(t)
    save_owned_credits(trs)