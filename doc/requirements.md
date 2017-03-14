# P2PAuto 系统设计板概要
## 愿景
2017年春节以来各排名靠前的P2P平台散标数量越来越少，而投资平台上的定期资产包也同样面临供不应求，且提前退出一般有90天后要求且有2%罚息。
本系统的目标是假设用户已经在平台上完成充值，本系统能够自动帮助用户分散投标，避免资金闲置。
## Backlog
### 1. 积木盒子自动投标
```
1) 散标首投项目自动投标
2) 散标债权转让项目自动投标, 自动使用加息券
```
### 2. 陆金所自动投标
```
1) 稳盈安e自动投标
2) 稳盈-e享自动投标
3) 稳盈-e享 -> 稳盈安e 套利
```
## 积木盒子网站操作流程分析
积木盒子网站采用服务器端编程技术，无法通过API获取JSON格式数据。因此在模拟用户操作时只能采用selenium方式编程。
### 1. 登陆
```
1) 打开URL: https://passport.jimubox.com/authentication/login?redirectUrl=https://www.jimu.com/User/AssetOverview
site:B662B0F090BE31C1DCB6A13D70E81429
username:brightg
password:111111
agreeContract:on
2) 输入用户名/登陆密码
3) 点击登陆按钮
```
### 2. 查询帐户余额
```
1) 打开资产总览页面https://www.jimu.com/User/AssetOverview
2) 读取可用余额，JSON XHR如下
https://www.jimu.com/User/AssetOverview/Asset?_=1488987431715
p2pUserInfo->totalP2pBalance
  
```
### 3. 债权转让自动投标
1) 查询债权转让项目，按金额排序
https://box.jimu.com/CreditAssign/List?orderIndex=2&

2) 读取转让项目链接和剩余天数
```
<a class="" href="/CreditAssign/Index/3961567" target="_blank">
    <div class="invest-item">

                        <span class="invest-item-profit">
                            323</span>
                    </div>
                    <div>剩余天数</div>
```         
3) 点击明细https://box.jimu.com/CreditAssign/Index/:item-id

4) 查询可用余额
```
  <div class="tip">
      可用余额：0.01元
      <a href="javascript:" id="act_project_all_in" class="pull-right" data-user-avaliable="0.01" data-avaliable="92.03">[全投]</a>
  </div>
```  
2. 点击全投, 同上元素


2. 同意转让协议
```
<input type="checkbox" id="Contract" name="Contract" required="" aria-required="true">
```
3. 点击一键转让
```
<button class="btn btn-primary" type="submit" id="act_project_invest" data-auto-investment-status="opened">一键投标</button>
```
