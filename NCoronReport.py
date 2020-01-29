#!/usr/bin/python3
import re
import sys
import time
import datetime
import requests
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from subprocess import call
from selenium.webdriver.firefox.options import Options

class NovelCronvReport():
    "2019nCov-武汉新型冠状病毒疫情报告信息采集类"
    def __init__(self, province=''):
        self.headers  = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
                           AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                          'Connection':'close'
                        }                                          #header可自行调整
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
            fobj.write('报告制作：Shieber\n')
            fobj.write('更新频率：每三小时自动更新\n')
            fobj.write('数据来源：腾讯疫情报告中心\n')
            fobj.write('生成时间：' + self.GetTime()  +'\n')
            fobj.write('数据地址：' + self.url + '\n')
            fobj.write('源码(国内)：https://gitee.com/QMHTMY/Coronavirus (码云)\n')
            fobj.write('源码(国外)：https://github.com/QMHTMY/Coronavirus (github)\n')
            fobj.write('PDF报告获取：以"疫情"为主题发送邮件到Shieber@aliyun.com获取PDF文件\n\n')

            #中国数据写入
            fobj.write('区域\t\t确诊\t疑似\t治愈\t死亡\n')
            fobj.write('中国' + '\t\t' + '\t'.join([cD[0],cD[1],cD[2],cD[3],'\n']))

            #外国数据写入
            for k, v in fD.items():
                if len(k) < 4:
                    fobj.write(k + '\t\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
                else:
                    fobj.write(k + '\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
            fobj.write('\n\n')

            #各省数据写入
            now = datetime.datetime.now()
            fobj.write('区域\t\t确诊\t治愈\t死亡\t%s日新增\n'%str(now.day-1))
            for dic in pD:
                for k, v in dic.items():
                    if len(k) < 4:
                        fobj.write(k + '\t\t' + '\t'.join([v[0],v[2],v[3],v[1],'\n']))
                    else:
                        fobj.write(k + '\t' + '\t'.join([v[0],v[2],v[3],v[1],'\n']))
                fobj.write('\n')
        
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
        call('Addmark %s temp.pdf watermark.pdf'%pdfName,shell=True)
        call('mv temp.pdf %s 1>/dev/null 2>&1'%pdfName,shell=True)

        #发送到邮箱
        #call('Email2phone %s 1>/dev/null 2>&1'%pdfName,shell=True)

if __name__ == '__main__':
    NCR  = NovelCronvReport()
    soup = NCR.GetFromURL()
    cd,pd,fd = NCR.ExtractData(soup)
    NCR.write2text(cd,pd,fd)
    NCR.trans2pdf()
