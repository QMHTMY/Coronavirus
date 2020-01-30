#!/usr/bin/python3
#-*- coding: utf-8 -*-
#
#    Author: Shieber
#    Date: 2020.01.30
#
#                             MIT LICENSE
#
#    Copyright (c) 2017 lymslive
#
#    Permission is hereby granted, free of charge, to any person obtaining a copy
#    of this software and associated documentation files (the "Software"), to deal
#    in the Software without restriction, including without limitation the rights
#    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
#    copies of the Software, and to permit persons to whom the Software is
#    furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in all
#    copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
#    SOFTWARE.
#
#                            Function Description
#    2019-nCoV武汉新型冠状病毒病例统计
#
#    Copyright 2020 
#    All Rights Reserved!

import re
import sys
import datetime
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from subprocess import call

class NovelCronvReport():
    "2019nCov-武汉新型冠状病毒疫情报告信息采集类"
    def __init__(self, province=''):
        self.author= 'Shieber'                                     #作者名
        self.name  = '2019_nConv'                                  #PDF文件名
        self.title = '2019-nCoV武汉新型冠状病毒疫情数据报告'       #PDF文件抬头
        self.url   = 'https://news.qq.com//zt2020/page/feiyan.htm' #Tecent报道url

    def GetTime(self):
        "报告时间"
        now = datetime.datetime.now()
        y, M, d = str(now.year), str(now.month),  str(now.day)
        h, m, s = str(now.hour), str(now.minute), str(now.second)

        #时间补0
        if now.month < 10:
            M = ''.join(['0',M]) 
        if now.day < 10: 
            d = ''.join(['0',d])
        if now.hour < 10: 
            h = ''.join(['0',h])
        if now.minute < 10: 
            m = ''.join(['0',m])
        if now.second < 10: 
            s = ''.join(['0',s])

        return '%s.%s.%s %s:%s:%s'%(y,M,d,h,m,s)

    def GetFromURL(self):
        "网页下载"
        fOpts = Options()
        fOpts.add_argument('--headless')
        driver = webdriver.Firefox(firefox_options=fOpts)
        driver.implicitly_wait(10)
        try: 
            driver.get(self.url)
            htmlCtnt = driver.page_source
            soup = Soup(htmlCtnt,'html.parser') 
        except Exception as err:
            print(err)
        finally:
            driver.close() 
            if soup:
                return soup
            else:
                print("NontType ")
                sys.exit(1)

    def ExtractData(self, soup):
        "从html中提取信息并保存"
        #1.全国总数据
        countyData = [] 
        divCountry = soup.find('div', attrs={'class':'recentNumber'})
        divNumbers = divCountry.find_all('div',attrs={'class':'number'})
        for divNumber in divNumbers:
            countyData.append(divNumber.getText().strip())

        #2.各省市自治区特别行政区(含港澳台)数据
        provsData = [] 
        divPlaces = soup.find('div',attrs={'class':'places'})

        divHubei  = divPlaces.find('div',attrs={'class':'placeItemWrap current'}) #湖北
        divProvs  = divPlaces.find_all('div',attrs={'class':'placeItemWrap '})
        divProvs.insert(0,divHubei)

        for divProv in divProvs:
            provData  = {} 

            #2.2.1一省区市总数据
            prov = divProv.find('div',attrs={"class":re.compile(r'clearfix placeItem placeArea.*?')}) 
            data = self.GetInfo(prov)
            provData[data[0]] = [data[2],data[1], data[3],data[4]]

            #2.2.2各省区市受感染城市数据
            infoItems = divProv.find_all('div',attrs={"class":"clearfix placeItem placeCity"})
            if infoItems:
                for infoItem in infoItems:
                    data = self.GetInfo(infoItem)
                    provData[data[0]] = [data[2],data[1],data[3],data[4]]
            provsData.append(provData)

        #3.国外数据
        frnsData = {}
        divFrns  = divPlaces.find_all('div',attrs={'class':'clearfix placeItem placeArea no-sharp abroad'})
        for divFrn in divFrns:
            data = self.GetInfo(divFrn)
            frnsData[data[0]] = [data[1],'x',data[2],data[3]]

        return countyData, provsData, frnsData

    def GetInfo(self, info):
        data = []

        #地区名
        h2 = info.find('h2')
        data.append(h2.getText().strip())

        #新增，确诊，治愈，死亡人数
        divs = info.find_all('div')
        for div in divs:
            data.append(div.getText().strip())

        return data

    def write2text(self, cD,pD,fD):
        "cD:全国数据,pD:各省数据,fD:国外数据"
        with open(self.name + '.txt','w') as fobj:
            #初始化标题等标准信息
            fobj.write(self.title +'\n')
            fobj.write('报告制作：%s\n'%self.author)
            fobj.write('数据来源：腾讯疫情实时追踪\n')
            fobj.write('生成时间：' + self.GetTime()  +'\n')
            fobj.write('数据地址：' + self.url + '\n')
            fobj.write('源码(国内)：https://gitee.com/QMHTMY/Coronavirus (码云)\n')
            fobj.write('源码(国外)：https://github.com/QMHTMY/Coronavirus (github)\n')
            fobj.write('\n')

            #中国总数据写入
            fobj.write('区域\t\t确诊\t疑似\t治愈\t死亡\t致死率\n')
            drate = self.deathRate(cD)
            fobj.write('中国'+'\t\t'+'\t'.join([cD[0],cD[1],cD[2],cD[3],drate'\n']))

            #外国总数据写入
            for k, v in fD.items():
                drate = self.deathRate(v)
                if len(k) < 4:
                    fobj.write(k + '\t\t' + '\t'.join([v[0],v[1],v[2],v[3],drate'\n']))
                else:
                    fobj.write(k + '\t' + '\t'.join([v[0],v[1],v[2],v[3],drate'\n']))
            fobj.write('\n\n')

            fobj.write('区域\t\t确诊\t治愈\t死亡\t致死率\t昨日确诊\n')#头一天日期
            #中国各省数据写入
            for dic in pD:
                for k, v in dic.items():
                    drate = self.deathRate(v)
                    if len(k) < 4:
                        fobj.write(k+'\t\t'+'\t'.join([v[0],v[2],v[3],drate,'+'+v[1],'\n']))
                    else:
                        fobj.write(k+'\t'+'\t'.join([v[0],v[2],v[3],'+'+v[1],'\n']))
                fobj.write('\n')

    def deathRate(self,data):
        #计算致死率
        if '0' != data[0]:
            rateStr = '%.1f%%'%(int(data[3])*100/int(data[0]))
        else:
            rateStr = 'x.xx%'
        return rateStr

        
    def trans2pdf(self):
        #转换为pdf并发送到邮箱
        txtName  = self.name + '.txt'
        docxName = self.name + '.docx'
        pdfName  = self.name + '.pdf'

        #转成Pdf
        call('Text2docx %s 1>/dev/null 2>&1'%txtName,shell=True)
        call('Docx2pdf %s 1>/dev/null 2>&1'%docxName,shell=True)
        call('rm %s 1>/dev/null 2>&1'%docxName,shell=True)

        #添加水印
        call('Addmark %s temp.pdf watermark.pdf -1 1'%pdfName,shell=True)
        call('mv temp.pdf %s 1>/dev/null 2>&1'%pdfName,shell=True)

        #发送到邮箱
        #call('Email2phone %s 1>/dev/null 2>&1'%pdfName,shell=True)

if __name__ == '__main__':
    NCR  = NovelCronvReport()
    soup = NCR.GetFromURL()
    cD,pD,fD = NCR.ExtractData(soup)
    NCR.write2text(cD,pD,fD)
    NCR.trans2pdf()
