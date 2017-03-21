# -*- coding: utf-8 -*-
import requests
import threading
import random
from pyquery.pyquery import fromstring
from pyquery import PyQuery as pq
import csv
from urllib2 import urlparse
import logging
import logging.config
import string
import argparse
import json
from os import sys, path
sys.path.insert(0,path.dirname(path.dirname(path.abspath(__file__))))
import utils
import config
import time
import datetime
from store import save_default_record, del_default_record
logging.config.dictConfig(config.LOGGING)
logger = logging.getLogger('wdqs')

JIMU_BASE_URL = "https://box.jimu.com"
JIMU_LOGIN_URL = "https://passport.jimubox.com/authentication/login?redirectUrl=https://www.jimu.com/User/AssetOverview"
JIMU_LOGIN_URL2 = "https://www.jimu.com/User/Ticket/Login/?ticket=%s&redirectUrl=https://www.jimu.com/User/AssetOverview"
JIMU_CHECK_BAL_URL = "https://www.jimu.com/User/AssetOverview/Asset?_=1488987431715"
JIMU_LIST_CREDIT_ASSIGN = "https://box.jimu.com/CreditAssign/List?orderIndex=2&"

# region 项目列表
def fetch_prj_list(session,url):
    """
        get prj list with status
    """
    
    rsp = session.get(url)
    return rsp.text

def parse_prj_list(html):
    """
        返回项目列表和下一页路径
    """
    root = pq(fromstring(html))
    ls_prj = []
    date_ = None
    hour_ = None
    for oel in root("a.invest-item"):
        title_ = pq(oel)("div.invest-item-title").text()
        if isinstance(title_ , unicode):
            title_ = unicode.encode(title_,"utf8")
        import re
        m = re.findall("(\d{6})-(\d{2})$",title_)
        if m:
            date_ = m[0][0]
            hour_ = m[0][1]
        date_ = ls_prj.append({
            "href": pq(oel).attr.href,
            "title":title_,
            "amount":pq(oel)("p.project-info span").text(),
            "interest":pq(oel)("span.invest-item-profit")[0].text.strip(),
            "term_months":pq(oel)("span.invest-item-profit")[1].text.strip(),
            "date":date_,
            "hour":hour_,
        })

    next_page_el = root("div.pagination.pagination-centered li.active").next()
    if next_page_el:
        next_page_url = next_page_el("a").attr.href
        next_page_url = urlparse.urljoin(JIMU_BASE_URL,next_page_url)
    return ls_prj,next_page_url

def get_prj_list(): 
    all_prj = []
    url = 'https://box.jimu.com/Project/List'
    max_pn = 1
    pidx = 0
    
    while url and pidx < max_pn: 
        logger.info("getting jimu projct info: " + url) 
        with requests.Session() as session:
            html = fetch_prj_list(session,url)
            ls_rpj,url = parse_prj_list(html)
            all_prj.extend(ls_rpj)
        pidx +=1
        
    with open("jimu_prj_list","w+") as file:
        w = csv.DictWriter(file,fieldnames=all_prj[0].keys(),dialect=csv.Dialect.delimiter)
        w.writeheader()
        w.writerows(all_prj)    
# endregion

#region 债权转让抢标
def login_jimu(session,user,psw):
    logger.info("logging jimu...")
    form = {"site":"B662B0F090BE31C1DCB6A13D70E81429",
           "username":user,
           "password":str(psw),
           "agreeContract":"on"}
    session.headers = {"Accept":"text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Content-Type":"application/x-www-form-urlencoded",
                "Origin":"https://passport.jimubox.com",
                "Cookie":"tr=71de397f-a081-4ced-9833-0d3be5e386ed; ps=e97df4d4-8469-4f12-aa89-4f23c1e10c7b-p",
                "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
                "Referer":"https://passport.jimubox.com/authentication/loginForm?site=B662B0F090BE31C1DCB6A13D70E81429&redirectUrl=https%3A%2F%2Fwww.jimu.com%2FUser%2FAssetOverview",
            }
    
    rsp = session.post(JIMU_LOGIN_URL,form)
    if rsp.status_code >= 400:
        raise Exception("Login Error")
    import re
    m = re.findall('ticket = "(\S+)"',rsp.text)
    if not m:
        raise Exception("Login Error")
    key = m[0]
    url = JIMU_LOGIN_URL2 % (key)
    session.headers = {}
    rsp = session.get(url)
    if rsp.status_code >= 400:
        raise Exception("Login Error")

def check_balance(session):
    """
        返回帐户余额
    """
    session.headers = {"Accept":"application/json, text/javascript, */*; q=0.01"}
    rsp = session.get(JIMU_CHECK_BAL_URL)
    jsret = json.loads(rsp.text)
    session.headers = {}
    return jsret["p2pUserInfo"]["totalP2pBalance"]

def get_credit_assigns(session):
    """
        查询债权转让项目，按金额排序
    """
    logger.debug("query credit assigns...")
    ls_credits = []
    rsp = session.get(JIMU_LIST_CREDIT_ASSIGN)
    stret = rsp.text
    q = pq(fromstring(stret))
    ttl_amt = 0
    for each in q("div.container.credit-assign-list a[@href*='/CreditAssign/Index']"):
        each = pq(each)
        amt0 = float(each("p.project-info span.decimal")[0].text.replace(',',''))
        amt1 = float(each("p.project-info span.decimal")[1].text.replace(',',''))
        amt0 = amt1 - amt0
        ttl_amt += amt1
        logger.info("credit: %.2f,%.2f" % (amt0,amt1))
        ls_credits.append({"url":urlparse.urljoin(JIMU_BASE_URL,each.attr.href),
             "amount": amt1,
             "bal":amt0,
             "interest_rate": float(each("div.invest-item-feature span.invest-item-profit")[0].text),
             "remain_days": int(each("div.invest-item-feature span.invest-item-profit")[1].text.replace(',','')),
            })
    if len(ls_credits) > 0:
        logger.info("total credit#: %d, amount:%.2f" % (len(ls_credits),ttl_amt))
    return ls_credits

def bid_credit_post(session,credit,bal):
    id = credit['url'].rsplit('/',1)[1]
    amt = credit['bal']
    if bal < amt:
      amt = bal
    session.post("https://box.jimu.com/CreditAssign/fastInvest" ,\
        {'CreditAssignID':id,'InvestAmount':amt,'Contract':'on'})
    logger.info('bid success:' + credit['url'])
    

def bid_credit_auto(session,url):
    
    import mechanize
    import traceback
    
    br = mechanize.Browser()
    br.set_cookiejar(session.cookies)
    user_agent = 'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)'
    br.addheaders = [('User-agent', user_agent)]
    
    br.set_handle_equiv(True)
    br.set_handle_gzip(True)
    br.set_handle_redirect(True)
    br.set_handle_referer(True)
    br.set_handle_robots(False)

    try:
        br.open(url)
        html = br.response().read()
        with open("bid.html",'w') as f:
            f.write(html)
        logger.info("biding credit: %s..." % url)
        br.select_form(nr=0)
        br.follow_link(text="[全投]")
        br.form.find_control(id="Contract").toggle()
        br.submit()
    except Exception, ex:
        logger.critical(str(ex))
        
        traceback.print_exec()

def bid_credit_assign():
    user = config.user
    psw = config.password
    with requests.Session() as session:
        login_jimu(session,user,psw)
        while True:
            acct_bal = check_balance(session)        
            credits = get_credit_assigns(session)
            if acct_bal < 300:
                continue

        for each in credits:
            if  each['bal'] > 300 and each['remain_days'] > 30 and each['interest_rate'] >= 8.5:  
                bid_credit_post(session,each,acct_bal)
            time.sleep(3)
#endregion
def fetch_default_records(session,dtext):
    """
        get prj list with status
    """
    page = 1
    ls_dr = []
    
    while True:
        url = "https://box.jimu.com/RepaymentPlan/List?page=%d&selectedReplaymentPlanType=0&selectedReplaymentPlanStatus=1&month=%s&date=" % (page,dtext)
        rsp = session.get(url)
        page +=1
        if rsp.status_code == 200:
            # parse
            q = pq(rsp.text)
            trs = q('table.table.payback-table tbody tr')
            if not trs:
                break
            for tr in trs[:-1]:
                dtxt = pq(tr)('td')[0].text
                amount = pq(tr)('td')[2].text
                type = pq(tr)('td')[4].text
                prj_name = pq(tr)('td')[5].text
                prj_id = pq(tr)('td:nth-child(6) a').attr.href
                d_ = datetime.datetime.strptime(dtxt,"%Y-%m-%d")
                
                if d_<datetime.datetime.today() and prj_id:
                    prj_id = prj_id.split('/')[-1]
                    ls_dr.append({'date':d_,
                                  'amount':amount,
                                  'type':type,
                                  'prj_id':prj_id,
                                  'prj_name':prj_name})
        else:
            break
    return ls_dr

def collect_default_records():
    user = config.user
    psw = config.password
    d_ = datetime.date.today()
    d_ = datetime.date(d_.year,d_.month,1)
    dtext = d_.strftime("%Y-%m-%d")
    with requests.Session() as session:
        login_jimu(session,user,psw)
        lsdr = fetch_default_records(session,dtext)
    del_default_record(d_)
    save_default_record(lsdr)    

def main():
    parser = argparse.ArgumentParser(description='Jimu Box Utility command')
    parser.add_argument('-b','--bid', action="store_true", help='Bid for credit assign')
    parser.add_argument('-l','--listproject', action="store_true", help='list credit project')
    parser.add_argument('-d','--default', action="store_true", help='Collect default record')
    
    args = parser.parse_args()
    if args.bid:
        bid_credit_assign()
    if args.default:
        collect_default_records()
    elif args.listproject:
        get_prj_list()

if __name__ == "__main__":
    import sys
    
    main()
