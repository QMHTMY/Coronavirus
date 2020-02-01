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

import sys
import time
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from subprocess import call
from selenium.webdriver.firefox.options import Options

class NovelCronvReport():
    "2019nCov-武汉新型冠状病毒疫情报告信息采集"
    def __init__(self, province=''):
        self.name  = '2019_nConv'                                  #PDF文件名
        self.title = '2019-nCoV武汉新型冠状病毒疫情数据报告'       #PDF文件抬头
        self.url   = 'https://news.qq.com//zt2020/page/feiyan.htm' #Tecent报道url

    def GetFromURL(self):
        "网页下载"
        fOpts = Options()
        fOpts.add_argument('--headless')
        driver = webdriver.Firefox(firefox_options=fOpts)
        driver.implicitly_wait(10)
        try: 
            driver.get(self.url)
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
        "从soup中提取信息并保存"
        #1.中国总数据
        CTData  = {} 
        divCN   = soup.find('div', attrs={'class':'recentNumber'})
        divNums = divCN.find_all('div',attrs={'class':'number'})
        CTData['中国'] = [div.getText().strip() for div in divNums]

        #2.各省市自治区特别行政区(含港澳台)数据
        divPlaces = soup.find('div',attrs={'class':'places'})
        divHubei  = divPlaces.find('div',attrs={'class':'placeItemWrap current'}) 
        divProvs  = divPlaces.find_all('div',attrs={'class':'placeItemWrap '})
        divProvs.insert(0,divHubei)

        provsData = [] 
        for divProv in divProvs:
            provData  = {'省':[],'市':{}} 
            #2.2.1一省区市总数据
            prov = divProv.find('div',attrs={"class":"clearfix placeItem placeArea"}) 
            data = self.GetInfo(prov)
            data[1],data[2] = data[2],data[1]
            provData['省'] = data

            #2.2.2各省区市受感染城市数据
            infoItems = divProv.find_all('div',attrs={"class":"clearfix placeItem placeCity"})
            for infoItem in infoItems:
                data = self.GetInfo(infoItem)
                data[1],data[2] = data[2],data[1]
                provData['市'][data[0]] = data[1:]
            provsData.append(provData)

        #3.外国数据
        divFrns  = divPlaces.find_all('div',attrs={'class':'clearfix placeItem placeArea no-sharp abroad'})
        for divFrn in divFrns:
            data = self.GetInfo(divFrn)
            CTData[data[0]] = [data[1],'0',data[2],data[3]]

        CTData = sorted(CTData.items(), key=lambda v: int(v[1][0]),reverse=True)
        return CTData, provsData

    def GetInfo(self, k):
        data = [k.find('h2').getText().strip()]  #地区
        divs = k.find_all('div')                 #新增，确诊，治愈，死亡人数
        data += [div.getText().strip() for div in divs]
        return data

    def statics(self, data): 
        t0,t1,t2,t3 = 0,0,0,0
        for k in data:
            t0 += int(k[1][0])
            t1 += int(k[1][1])
            t2 += int(k[1][2])
            t3 += int(k[1][3])
        return [str(t0), str(t1), str(t2), str(t3)]

    def infectedNum(self, data):
        #统计各省区市死亡数
        ifNum, dDis = {}, {}
        for dic in data:
            pd = dic['省']
            ifNum[pd[0]] = pd[1]
            if '0' != pd[-1]:
                dDis[pd[0]] = pd[-1]

        ifNum = sorted(ifNum.items(),key=lambda v:int(v[1]),reverse=True)
        dDis  = sorted(dDis.items(),key=lambda v: int(v[1]),reverse=True)
        return ifNum, dDis
        
    def serverCity(self, provsD):
        #计算感染数过百的市区县
        ov100 = {}
        for dic in provsD:
            ctD = dic['市']
            for k, v in ctD.items():
                if 100 < int(v[0]):
                    ov100[k] = [v[0], dic['省'][0]]

        ov100 = sorted(ov100.items(), key=lambda v: int(v[1][0]),reverse=True)
        return ov100

    def dRate(self,data):
        #计算致死率
        data = data[-4:]
        if '0' != data[0]:
            rateStr = '%.1f%%'%(int(data[-1])*100/int(data[0]))
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
        #call('Addmark %s temp.pdf watermark_1.pdf'%pdfName,shell=True)
        #call('mv temp.pdf %s 1>/dev/null 2>&1'%pdfName,shell=True)

        #发送到邮箱
        #call('Email2phone %s 1>/dev/null 2>&1'%pdfName,shell=True)

    def sars(self, fobj):
        fobj.write('\n2003年SARS疫情最终数据(WHO)：\n')
        fobj.write('区域\t\t确诊\t死亡\t致死率\n')
        fobj.write('大陆\t\t5327\t349\t6.6%\n')
        fobj.write('香港\t\t1755\t300\t17.1%\n')
        fobj.write('台湾\t\t665\t180\t27.1%\n')
        fobj.write('中国\t\t7747\t829\t10.7%\n')
        fobj.write('全球\t\t8422\t919\t10.9%\n')

    def write2text(self, cD, provsD):
        "cD:全国数据,pD:各省数据,fD:国外数据"
        with open(self.name + '.txt','w') as fobj:
            #1.初始化标题等标准信息
            timestr = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
            fobj.write(self.title +'\n')
            fobj.write('报告时间：' + timestr +'\n')
            fobj.write('数据来源：腾讯疫情实时追踪\n')
            fobj.write('数据地址：' + self.url + '\n')

            #2.统计全球数据
            aD = self.statics(cD)     #全球总计
            fD = self.statics(cD[1:]) #国外总计
            zD = cD[0][1]             #中国总计
            fobj.write('\nA. 2019-nCoV疫情报告摘要：')
            fobj.write('\n区域\t确诊\t疑似\t治愈\t死亡\t致死率\n')
            fobj.write('中国'+'\t'+'\t'.join([zD[0],zD[1],zD[2],zD[3],self.dRate(zD),'\n']))
            fobj.write('外国'+'\t'+'\t'.join([fD[0],fD[1],fD[2],fD[3],self.dRate(fD),'\n']))
            fobj.write('全球'+'\t'+'\t'.join([aD[0],aD[1],aD[2],aD[3],self.dRate(aD),'\n']))

            #3.统计出现死亡区域及各省区市确诊数
            ifNum, dDis = self.infectedNum(provsD)
            fobj.write('\n出现死亡病例省区市：\n')
            for dd in dDis:
                fobj.write(''.join([dd[0],'：',dd[1],'\n']))

            fobj.write('\n各省区市确诊人数：\n')
            for i in range(17):      #34个省区市，分成两列
                p1, p2 = ifNum[i], ifNum[i+17]
                fobj.write(''.join([p1[0],'：',p1[1],'\t',p2[0],'：',p2[1],'\n']))

            #4.统计确诊数过百的城市
            ov100 = self.serverCity(provsD)
            fobj.write('\n确诊人数过百的城市:\n')
            for i, item in enumerate(ov100):
                num = str(i+1) if i+1 >= 10 else '0' + str(i+1)
                fobj.write(''.join([num,item[1][1],'・',item[0],'：',item[1][0],'\n']))

            #5.全球各国和中国详细数据
            fobj.write('\nB. 2019-nCoV疫情各国详细数据：')
            fobj.write('\n区域\t\t确诊\t疑似\t治愈\t死亡\t致死率\n')
            for item in cD:
                k, v = item[0], item[1]
                dli = '\t\t' if len(k) < 4 else '\t'
                fobj.write(k + dli + '\t'.join([v[0],v[1],v[2],v[3],self.dRate(v),'\n']))

            #6.中国各省详细数据
            fobj.write('\nC. 2019-nCoV疫情各省区市详细数据：')
            fobj.write('\n区域\t\t确诊\t治愈\t死亡\t致死率\t昨日确诊\n')
            for dic in provsD:
                v   = dic['省']
                new = v[2] if '-' in v[2] else '+' + v[2]
                dli = '\t\t' if len(v[0]) < 4 else '\t'
                fobj.write(v[0] + dli + '\t'.join([v[1],v[3],v[4],self.dRate(v),new,'\n']))

                cds = dic['市']
                for k,v in cds.items():
                    new = v[1] if '-' in v[1] else '+' + v[1]
                    dli = '\t\t' if len(k) < 4 else '\t'
                    fobj.write(k + dli + '\t'.join([v[0],v[2],v[3],self.dRate(v),new,'\n']))
                fobj.write('\n')

if __name__ == '__main__':
    NCR  = NovelCronvReport()
    soup = NCR.GetFromURL()
    cD,pD = NCR.ExtractData(soup)
    NCR.write2text(cD,pD)
    NCR.trans2pdf()
