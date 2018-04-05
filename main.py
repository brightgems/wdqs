# -*- coding: utf-8 -*-
#==================
# Author:
# History:
#   1/28 ignore overdue project when biding
#   1/29 retrieve project detainl of my own projects
#==================
import requests
import random
from pyquery.pyquery import fromstring
from pyquery import PyQuery as pq
import lxml.html
import urlparse

import logging
import logging.config
import argparse
import json
from os import sys, path
sys.path.insert(0, path.dirname(path.dirname(path.abspath(__file__))))

import config
import time
import datetime
import math
from requests.packages.urllib3.exceptions import InsecureRequestWarning

# fix SSL bad handshake
import requests.packages.urllib3.util.ssl_
print(requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS)
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

from store import save_default_record, del_default_record, save_owned_credits, save_credit_projects, save_project_details

logging.config.dictConfig(config.LOGGING)
logger = logging.getLogger('wdqs')

JIMU_BASE_URL = "https://box.jimu.com"

JIMU_LOGIN_URL = "https://www.jimu.com/User/Login"
JIMU_CHECK_BAL_URL = "https://www.jimu.com/User/AssetOverview/Asset?_=1488987431715"
JIMU_LIST_CREDIT_ASSIGN = "https://box.jimu.com/CreditAssign/List?rate=10&days={0}&orderIndex=1"
JIMU_PRJ_DETAILS = "https://box.jimu.com/Project/Index/{0}"

JIMU_REQUEST_HEADERS = {
    "Accept":
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Content-Type":
    "application/x-www-form-urlencoded",
    "Upgrade-Insecure-Requests":
    "1",
    "DNT":
    "1",
    "Origin":
    "https://box.jimu.com",
    "Cookie":'tr=102b2826-5546-4d77-a5f6-1bc4910cc0c7; tr=ce7798f2-6be6-40c9-8165-4601819f163c; gr_user_id=7bc5a3a0-4737-4e09-9447-f9d6eea8dd96; _qzja=1.1636350280.1501763703516.1501763703516.1501767982886.1501768000969.1501768122182.0.0.0.5.2; __utma=237340443.178906233.1497061582.1501767983.1501856196.7; _jzqa=1.3851647976868439600.1501763703.1501767983.1501856196.3; ag_fid=ejFkst1Z4xaLMP1F; __ag_cm_=1; Hm_lvt_1dc096a18210fb74c17c2feb1eb75e9c=1522847413,1522891871; Hm_lvt_b52e68eb56d57aeecdafc769040770d4=1522847413,1522891871; gr_session_id_82dbda8cf8253e8f=5c387eb2-5923-442a-a535-ed373ee341dd; ps=64ceaa25-253d-494d-a141-ab50d76eaa1b-p; bs=9e22b4b8-f69c-4094-9c65-5d866e96d7e0-w; .TLFT=JqYGsollrxAkGC0E06w4qA%3D%3D%3APdYGxR2bfxDi7rIgDIj0%2Fhpu9OYoJ%2BXEn0F7muPL5kU%3D%3A4%2FB%2FSl3OGsNIecDQZInkkBhN%2FH638qY5Y%2FT9qjRZwieEE%2Fr8oxtboPOywK%2BJ3vt1; Hm_lpvt_1dc096a18210fb74c17c2feb1eb75e9c=1522892881; Hm_lpvt_b52e68eb56d57aeecdafc769040770d4=1522892881',
    "User-Agent":
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36",
    "Referer":
    "https://passport.jimubox.com/authentication/loginForm?site=B662B0F090BE31C1DCB6A13D70E81429&redirectUrl=https%3A%2F%2Fwww.jimu.com%2FUser%2FAssetOverview",
}

# region 项目列表

def fetch_prj_list(session, url):
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
        if isinstance(title_, unicode):
            title_ = unicode.encode(title_, "utf8")
        import re
        m = re.findall("(\d{6})-(\d{2})$", title_)
        if m:
            date_ = m[0][0]
            hour_ = m[0][1]
        date_ = ls_prj.append({
            "href":
            pq(oel).attr.href,
            "title":
            title_.decode('utf-8', 'ignore'),
            "amount":
            re.findall('[0-9\.]+',
                       pq(oel)("p.project-info span").text().split('/')[-1]
                       .strip())[0],
            "interest":
            pq(oel)("span.invest-item-profit")[0].text.strip(),
            "term_months":
            pq(oel)("span.invest-item-profit")[1].text.strip(),
            "date":
            date_,
            "hour":
            hour_,
        })

    next_page_el = root("div.pagination.pagination-centered li.active").next()
    if next_page_el:
        next_page_url = next_page_el("a").attr.href
        next_page_url = urlparse.urljoin(JIMU_BASE_URL, next_page_url)
    return ls_prj, next_page_url


def get_prj_list():
    all_prj = []
    url = 'https://box.jimu.com/Project/List'
    max_pn = 100
    pidx = 0

    while url and pidx < max_pn:
        logger.info("getting jimu projct info: " + url)
        with requests.Session() as session:
            html = fetch_prj_list(session, url)
            ls_rpj, url = parse_prj_list(html)
            all_prj.extend(ls_rpj)
        pidx += 1
    save_credit_projects(all_prj)

def get_credit_prj_list():
    user = config.user
    psw = config.password
    url_template = "https://box.jimu.com/CreditAssign/List?amount=&repaymentCalcType=&category=&rate=&days=&page={0}&orderIndex=1&guarantee="
    with requests.Session() as session:
        login_jimu(session, user, psw)

        logger.debug('logging success!')
        page = 1
        visited_prjs = {}
        while True:
            logger.debug('reading credit assign page {%d}..!' % page)
            credit_url = url_template.format(page)
            rsp = session.get(credit_url, verify=False)
            html = rsp.text
            ls_credits = parse_credit_assign(html)
            if len(ls_credits) == 0:
                break

            ls_prjid= set()
            for each in ls_credits:
                prj_id = get_origion_prj_id(session, each['url'])
                if not visited_prjs.has_key(prj_id):
                    ls_prjid.add(prj_id)
                    visited_prjs[prj_id] = 1

            ls_prjdt = get_project_details(session, ls_prjid)
            save_project_details(ls_prjdt)
            page +=1

# endregion

def login_jimu_browser(session):
    br = JimuBrowser()
    ck_str = br.init_api()
    JIMU_REQUEST_HEADERS['Cookie'] = ck_str
    rsp = session.get(JIMU_CHECK_BAL_URL, headers=JIMU_REQUEST_HEADERS)
    if rsp.status_code >= 400:
        raise Exception("Login Error")
    import re
    m = re.findall('ticket = "(\S+)"', rsp.text)
    if not u'上次登录' in rsp.text:
        raise Exception("Login Error")
        

# region 债权转让抢标

def login_jimu(session, user, psw):
    logger.info("logging jimu...")
    form = {
        "site": "",
        "username": user,
        "password": str(psw),
        "agreeContract": "on"
    }

    rsp = session.post(JIMU_LOGIN_URL,
        form,
        headers=JIMU_REQUEST_HEADERS,
        verify=False,
        timeout=10)

    if rsp.status_code >= 400:
        raise Exception("Login Error")
    import re
    m = re.findall('ticket = "(\S+)"', rsp.text)
    if not u'上次登录' in rsp.text:
        raise Exception("Login Error")
    # if not m:
    #    raise Exception("Login Error")
    #key = m[0]
    #url = JIMU_LOGIN_URL0 % (key)
    #session.headers = {}
    #rsp = session.get(url)
    # if rsp.status_code >= 400:
    #    raise Exception("Login Error")

def check_balance(session):
    """
        返回帐户余额
    """
    session.headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01"
    }
    rsp = session.get(JIMU_CHECK_BAL_URL)
    jsret = json.loads(rsp.text)
    session.headers = {}
    return jsret["p2pUserInfo"]["totalP2pBalance"]


def get_credit_assigns(session):
    """
        查询债权转让项目，按金额排序
    """
    logger.debug("query credit assigns...")
    
    url_ls = [JIMU_LIST_CREDIT_ASSIGN.format(days) for days in [11, 12, 13]]
    if datetime.datetime.now().hour in [11, 16, 22, 23]:
        url_ls = ['https://box.jimu.com/CreditAssign/List?rate=9&amount=3&days=13&orderIndex=1',
            'https://box.jimu.com/CreditAssign/List?days=14&amount=3&rate=10&orderIndex=1',
            'https://box.jimu.com/CreditAssign/List?days=15&amount=3&rate=10&orderIndex=1',
            'https://box.jimu.com/CreditAssign/List?rate=10&amount=3&days=14&orderIndex=1',
            'https://box.jimu.com/CreditAssign/List?days=12&amount=3&rate=9&orderIndex=1']

    credit_url = random.choice(url_ls)
    rsp = session.get(credit_url, verify=False)
    stret = rsp.text
    ls_credits = parse_credit_assign(stret)
    
    return ls_credits

def parse_credit_assign(html):
    q = pq(fromstring(html))
    ttl_amt = 0
    ls_credits = []
    for each in q("div.container.credit-assign-list a[@href*='/CreditAssign/Index']"):
        each = pq(each)
        amt0 = float(each("p.project-info span.decimal")[0].text.replace(',', ''))
        amt1 = float(each("p.project-info span.decimal")[1].text.replace(',', ''))
        amt0 = amt1 - amt0
        ttl_amt += amt1
        logger.debug("credit: %.2f,%.2f" % (amt0, amt1))
        ls_credits.append({
            "url":
            urlparse.urljoin(JIMU_BASE_URL, each.attr.href),
            "amount":
            amt1,
            "bal":
            amt0,
            "interest_rate":
            float(each("div.invest-item-feature span.invest-item-profit")[0]
                .text),
            "remain_days":
            int(each("div.invest-item-feature span.invest-item-profit")[1]
                .text.replace(',', '')),
            "title":
            each("div.invest-item-subtitle").text()
        })

    if len(ls_credits) > 0:
        logger.info("total credit#: %d, amount:%.2f" % (len(ls_credits),
                                                    ttl_amt))
    return ls_credits

def bid_credit_post(session, credit, bal):
    id = credit['url'].rsplit('/', 1)[1]
    amt = credit['bal']
    if bal < amt:
        amt = bal
    # 单个项目最高不超过3000
    amt = '%.2f' % min(amt, 3000)
    # confim
    #session.headers= JIMU_REQUEST_HEADERS
    session.headers['DNT'] = '1'
    session.headers['Referer'] = 'https://box.jimu.com/CreditAssign/CreditAssignConfirm'
    session.headers['Upgrade-Insecure-Requests'] = '1'
    rsp = session.get('https://box.jimu.com/CreditAssign/Index/%s' % str(id))
    # time.sleep(random.randint(2,4))
    rsp = session.post('https://box.jimu.com/CreditAssign/CreditAssignConfirm',
        {'CreditAssignID': id,
         'InvestAmount': amt},
        verify=False)
    time.sleep(random.randint(1, 4))
    rsp = session.post("https://box.jimu.com/CreditAssign/fastInvest",
        {'CreditAssignID': id,
         'InvestAmount': amt,
         'Contract': 'on'},
        verify=False)
    if rsp.status_code == 200:
        logger.info('bid success:' + credit['url'])
    else:
        logger.critical('bid error:' + credit['url'])
    # time.sleep(random.randint(3,7))


# 获取原始项目ID
def get_origion_prj_id(session, url):
    rsp = session.get(url)
    root = pq(fromstring(rsp.text))
    prj_href = root('#creditAssignData > div.row-fluid.credit-assign-content > div.span8 > div.credit-assign-title > h5 > a').attr.href
    return prj_href.split("/")[-1]


visited_prj = dict()


def bid_credit_assign():
    user = config.user
    psw = config.password
    with requests.Session() as session:
        login_jimu(session, user, psw)

        logger.debug('logging success!')
        while True:
            acct_bal = check_balance(session)
            logger.debug('bal:%f' % acct_bal)
            if acct_bal < 500:
                time.sleep(15 * 60)
                continue
            credits = get_credit_assigns(session)

            for each in credits:
                if acct_bal > 500 and each['bal'] > 500 \
                        and each['remain_days'] > 30 and each['remain_days'] < 400 and each['interest_rate'] >= 9.5:
                    # 检查是否有逾期
                    try:
                        if visited_prj.has_key(each['url']):
                            prj_id, should_bid = visited_prj[each['url']]
                        else:
                            prj_id = get_origion_prj_id(session, each['url'])
                            prj = fetch_prject_details(session, prj_id)
                            should_bid = prj and prj['overdueCount'] <= 2 # and prj['cardNum'] 
                            visited_prj[each['url']] = (prj_id, should_bid)

                        if should_bid:
                            bid_credit_post(session, each,
                                            acct_bal - 100)  # 预留100块余额
                            new_acct_bal = check_balance(session)
                            # 金额没有变化，可能是session过期
                            if new_acct_bal == acct_bal:
                                #logger.warn('bid failed!')
                                login_jimu(session, user, psw)
                            else:
                                acct_bal = new_acct_bal
                        else:
                            logger.info("Decline to bid on %s" % prj_id)
                    except Exception as ex:
                        logger.error("something error:" + str(ex))
            time.sleep(60)


# endregiona

def fetch_default_records(session, dtext):
    """
        get prj list with status
    """
    page = 1
    ls_dr = []

    while True:
        url = "https://box.jimu.com/RepaymentPlan/List?page=%d&selectedReplaymentPlanType=0&selectedReplaymentPlanStatus=1&month=%s&date=" % (page, dtext)
        rsp = session.get(url)
        page += 1
        if rsp.status_code == 200:
            # parse
            q = pq(rsp.text)
            trs = q('table.table.payback-table tbody tr')
            if not trs or len(trs) == 1:
                break
            for tr in trs[:-1]:
                dtxt = pq(tr)('td')[0].text
                amount = pq(tr)('td')[2].text
                type = pq(tr)('td')[4].text
                prj_name = pq(tr)('td')[5].text
                prj_id = pq(tr)('td:nth-child(6) a').attr.href
                d_ = datetime.datetime.strptime(dtxt, "%Y-%m-%d")

                if d_ < datetime.datetime.today() - datetime.timedelta(days=1) and prj_id:
                    prj_id = prj_id.split('/')[-1]
                    ls_dr.append({
                        'date': d_,
                        'month': dtext,
                        'amount': amount,
                        'type': type,
                        'prj_id': prj_id,
                        'prj_name': prj_name
                    })
            if d_ >= datetime.datetime.today():
                break
        else:
            break
    return ls_dr


def collect_default_records():
    user = config.user
    psw = config.password
    d_ = datetime.date.today()
    d_ = datetime.date(d_.year, d_.month, 1)
    dtext = d_.strftime("%Y-%m-%d")
    with requests.Session() as session:
        login_jimu(session, user, psw)
        lsdr = fetch_default_records(session, dtext)
    del_default_record(dtext)
    # 删除重复项目
    import pandas as pd
    df_dr = pd.DataFrame(lsdr)
    df_dr = df_dr.drop_duplicates(df_dr.columns[1:])
    lsdr = df_dr.to_dict(orient='records')
    save_default_record(lsdr)


# region owned_credits

def fetch_owned_credits(session):
    page = 1
    ls_oc = []
    logger.info("start fetch owned credits..")
    while True:
        url = "https://box.jimu.com/Account/CreditAssign/OwnedInvest?status=Repayment&page=%d&assignFlag=0&daysIndex=10&rateIndex=10&calcTypeIndex=0&holdAmountIndex=0&_t=%d" % (page, int(time.time()))
        rsp = session.get(url)

        if rsp.status_code == 200:
            # parse
            jsobj = json.loads(rsp.text)
            trs = jsobj['ownInvestList']
            if not trs:
                break
            ls_oc.extend(trs)
            logger.info("fetch owned credits page %d" % page)
        else:
            break
        page += 1
    return ls_oc


def get_owned_credits():
    user = config.user
    psw = config.password
    with requests.Session() as session:
        login_jimu(session, user, psw)
        lsoc = fetch_owned_credits(session)
        save_owned_credits(lsoc)
        ls_prjid = set([credit['projectID'] for credit in lsoc])
        
        ls_prjdt = get_project_details(session, ls_prjid)
        save_project_details(ls_prjdt)


# endregion


# region prject_details
def parse_amt(amtstr):
    amt = float(amtstr[:-2].replace(',', '').strip())
    if amtstr.endswith(u'万元'):
        return amt * 10000
    else:
        return amt

def parse_dt(dtstr):
    if len(dtstr)==10:
        return datetime.datetime.strptime(dtstr, "%Y-%m-%d")
    else:
        return datetime.datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")

def fetch_prject_details(session, prjId):
    logger.info("fetch project detail: %s" % prjId)

    url = JIMU_PRJ_DETAILS.format(prjId)
    rsp = session.get(url)
    prj = {}

    if rsp.status_code == 200:
        # parse html
        html = rsp.text
        root = lxml.html.fromstring(html)
        
        prj['projectID'] = prjId
        prj['projectName'] = root.cssselect("#ProjectBasicInfo > div:nth-child(3) > dl > dd")[0].text
        prj['userName'] = root.cssselect("#ProjectBasicInfo > div:nth-child(5) > dl > dd:nth-child(2)")[0].text
        # not get companyInfo/ ProjectInfo
        if not root.xpath("//*[@id='PersonalInfo']"):
            return

        borrowerName_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='姓名']")
        prj['borrowerName'] = borrowerName_elements[0].getnext().text.strip() if borrowerName_elements else ""
        prj['borrowerType'] = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='主体性质']")[0].getnext().text.strip()
        borrowerGender_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='性别']")
        prj['borrowerGender'] = borrowerGender_elements[0].getnext().text.strip() if borrowerGender_elements else ""

        prj['borrowerAge'] = int(root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='年龄']")[0].getnext().text[:-2])
        prj['workCity'] = root.cssselect("#ProjectBasicInfo > div:nth-child(6) > dl > dd:nth-child(2)")[0].text
        prj['repaymentMethod'] = root.cssselect("body > div.project-detail > div > div.row-fluid > article > div.project-basic-info > h5")[0].text
        cardNo_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='证件号码']")
        if cardNo_elements:
            prj['cardNum'] = cardNo_elements[0].getnext().text
        else:
            prj['cardNum'] = ""
        education_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='学历']")
        prj['education'] = education_elements[0].getnext().text if education_elements else ""
        marriage_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='婚姻状况']")
        prj['marriageStatus'] = marriage_elements[0].getnext().text if marriage_elements else ""
        
        loanApplyCity_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='贷款提交城市']")
        prj['loanApplyCity'] = loanApplyCity_elements[0].getnext().text if loanApplyCity_elements else ""

        incomeRange_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='收入范围']")
        prj['incomeRange'] = incomeRange_elements[0].getnext().text if incomeRange_elements else ""

        employerType_elements = root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='工作单位性质']")
        prj['employerType'] = employerType_elements[0].getnext().text if employerType_elements else ""

        prj['loanAmount'] = parse_amt(root.xpath(u"//*[@id='ProjectBasicInfo']/div/dl/dt[text()='本期融资金额']")[0].getnext().text)

        prj['loanMonth'] = int(root.xpath(u"//*[@id='ProjectBasicInfo']/div/dl/dt[text()='借款期限']")[0].getnext().text.strip(u"个月"))
        prj['overdueCount'] = int(root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='平台历史逾期次数']")[0].getnext().text[:-2])

        prj['historyOverdueAmount'] = parse_amt(root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='平台历史逾期金额']")[0].getnext().text)
        prj['currentOverdueAmount'] = parse_amt(root.xpath(u"//*[@id='PersonalInfo']/div/div/dl/dt[text()='平台当前逾期金额']")[0].getnext().text)
        loanStDt = root.xpath(u"//*[@id='ProjectBasicInfo']/div/dl/dt[text()='计划还款日期']")[0].getnext().text
        prj['loanStDt'] = parse_dt(loanStDt)
    return prj


# 获取贷款人详情和逾期
def get_project_details(session, idList):
    logger.info("start fetch project details..")
    ls_prj = []
    for id in idList:
        try:
            prj = fetch_prject_details(session, id)
            if prj:
                ls_prj.append(prj)
        except Exception as ex:
            logger.error("something error:" + str(ex))
    return ls_prj


# endregion

def main():
    parser = argparse.ArgumentParser(description='Jimu Box Utility command')
    parser.add_argument('-b', '--bid', action="store_true", help='Bid for credit assign')
    parser.add_argument('-l', '--listproject', action="store_true", help='list credit project')
    parser.add_argument('-d', '--default', action="store_true", help='Collect default record')
    parser.add_argument('-o', '--owned', action="store_true", help='owned credits')
    parser.add_argument('-t', '--test', action="store_true", help='test project detail')

    args = parser.parse_args()
    if args.bid:
        bid_credit_assign()
    if args.default:
        collect_default_records()
    elif args.listproject:
        get_credit_prj_list()
    elif args.owned:
        get_owned_credits()
    elif args.test:
        user = config.user
        psw = config.password
        
        with requests.Session() as session:
            login_jimu(session, user, psw)
            ls_prj = get_project_details(session, ['4139010'])
        save_project_details(ls_prj)
        print(ls_prj)


if __name__ == "__main__":
    import sys

    main()
