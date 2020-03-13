#!/usr/bin/python3
# -*- coding: utf-8 -*-

import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

chinaHTML   = 'nConvChina.html'   #国内感染数据
foreignHTML = 'nConvForeign.html' #国外感染数据
chinaURL    = 'https://news.qq.com//zt2020/page/feiyan.htm'         #Tecent疫情报道国内url
foreignURL  = 'https://news.qq.com//zt2020/page/feiyan.htm#/global' #Tecent疫情报道国际url

UHtpls = [(chinaURL, chinaHTML), (foreignURL, foreignHTML)]

def download():
    #网页下载
    fOpts = Options()
    fOpts.add_argument('--headless')
    driver = webdriver.Firefox(firefox_options=fOpts)
    driver.implicitly_wait(20)
    try: 
        for tpl in UHtpls:
            driver.get(tpl[0]) 
            #time.sleep(10)
            with open(tpl[1],'w') as fobj:
                fobj.write(driver.page_source)
    except Exception as err:
        print(err)
    finally:
        driver.close() 

    return chinaHTML, foreignHTML
