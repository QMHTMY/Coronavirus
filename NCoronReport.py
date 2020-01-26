#!/usr/bin/python
import re,sys
import time
import datetime
from bs4 import BeautifulSoup as Soup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from subprocess import call

class NovelCovReport():
    "2019nCov-武汉新型冠状病毒疫情报告信息采集类"
    def __init__(self, province=''):
        self.headers  = { 'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) \
                           AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
                          'Connection':'close'
                        }                                          #header可自行调整
        self.name  = '2019_nConv'                                  #PDF文件名
        self.title = '2019新型冠状病毒疫情数据报告'                #PDF文件抬头
        self.url   = 'https://news.qq.com//zt2020/page/feiyan.htm' #Tecent报道url

    def Time(self):
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

    def getFromURL(self):
        "网页下载"
        Ffopts = Options()
        Ffopts.add_argument('--headless') #无头浏览器
        driver = webdriver.Firefox(firefox_options=Ffopts)
        driver.implicitly_wait(10)
        try: 
            driver.get(self.url)
            #time.sleep(5)
            html_cont = driver.page_source
            soup = Soup(html_cont,'html.parser') 
        except Exception as err:
            print(err)
        finally:
            driver.close() 
            return soup

    def extractData(self, soup):
        "从html中提取信息并保存"
        if not soup:
            print("NontType ")
            sys.exit(1)

        #1.全国总数据
        countyData = [] 
        divcountry = soup.find('div', attrs={'class':'recentNumber'})
        divnumbers = divcountry.find_all('div',attrs={'class':'number'})
        for div in divnumbers:
            countyData.append(div.getText().strip())
        #['2034','2684','49','56']

        #2.其他省市自治区特别行政区(含港澳台)数据
        provsData = [] 
        divplaces = soup.find('div',attrs={'class':'places'})

        #2.1特殊地区
        divhubei = divplaces.find('div',attrs={'class':'place current'})        #湖北数据
        divhgat  = divplaces.find_all('div',attrs={'class':'place no-sharp '})  #沪港澳台数据

        #2.2其他各省区市
        divprovs = divplaces.find_all('div',attrs={'class':'place '})

        for div in divhgat:
            divprovs.insert(0,div) #沪港澳台数据加入
        divprovs.insert(0,divhubei) 

        for divprov in divprovs:
            #2.2.1一省区市总数据
            provData  = {} 
            Pdata = self.getProvData(divprov)
            provData[Pdata[0]] = [Pdata[1],'x', Pdata[2],Pdata[3]]

            #2.2.2各省区市受感染城市数据
            infoItems = divprov.find_all('div',attrs={'class':'infoItem'})
            if infoItems:
                for infoItem in infoItems:
                    Cdata = self.getCityData(infoItem)
                    provData[Cdata[0]] = [Cdata[1],'x', Cdata[2],Cdata[3]]
            provsData.append(provData)

        #3.国外数据
        foreignsData = {}
        divforeign  = divplaces.find_all('div',attrs={'class':'place no-sharp'})
        for country in divforeign:
            Fdata = self.getForeignData(country)
            foreignsData[Fdata[0]] = [Fdata[1],'x', Fdata[2],Fdata[3]]

        #4.数据返回
        return countyData, provsData,foreignsData

    def getForeignData(self,country):
        "提取它国数据"
        info = country.find('div',attrs={'class':'info'}) 
        return self.getinfo(info) #['泰国','6','2','0']

    def getProvData(self,divprov):
        "提取一省数据"
        info = divprov.find('div',attrs={'class':'info'}) 
        return self.getinfo(info) #['湖北','1052','42','52']

    def getCityData(self,infoItem):
        "提取一市数据"
        return self.getinfo(infoItem) #['武汉','618','42','52']

    def getinfo(self,item):
        datatext = item.getText().strip()
        datatext = datatext.replace('\n','').replace(' ','')
        dataPtn  = re.compile(r'(.*)确诊(.*)例，治愈(.*)例，死亡(.*)例') 
        match    = dataPtn.search(datatext)
        data     = [match.group(1),match.group(2),match.group(3),match.group(4)]
        return data

    def write2text(self, CD,PD,FD):
        "CD:全国,PD:各省,FD:国外"
        with open(self.name + '.txt','w') as fobj:
            #初始化标题等信息
            fobj.write(self.title +'\n')
            fobj.write(' '*10 + self.Time()  +'\n\n')
            fobj.write('区域\t\t确诊\t疑似\t治愈\t死亡\n')

            #中国数据写入
            fobj.write('中国' + '\t\t' + '\t'.join([CD[0],CD[1],CD[2],CD[3],'\n']))

            #外国数据写入
            for k, v in FD.items():
                if len(k) < 4: 
                    fobj.write(k + '\t\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
                else:          #国名太长就少打印一个\t，为了对齐
                    fobj.write(k + '\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
            fobj.write('\n')

            #各省数据写入
            for dic in PD:
                for k, v in dic.items():
                    if len(k) < 4:
                        fobj.write(k + '\t\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
                    else:      #市名太长就少打印一个\t
                        fobj.write(k + '\t' + '\t'.join([v[0],v[1],v[2],v[3],'\n']))
                fobj.write('\n')
        
    def trans2pdf(self):
        #转换为pdf
        txtname  = self.name + '.txt'
        docxname = self.name + '.docx'
        pdfname  = self.name + '.pdf'

        #调用自己编写好的系统指令转成Pdf
        call('Text2docx %s 1>/dev/null 2>&1'%txtname,shell=True)
        call('Docx2pdf %s 1>/dev/null 2>&1'%docxname,shell=True)
        call('rm %s 1>/dev/null 2>&1'%docxname,shell=True)

        #调用自己编写好的系统指令添加水印
        call('Addmark %s temp.pdf watermark.pdf'%pdfname,shell=True)
        call('mv temp.pdf %s 1>/dev/null 2>&1'%pdfname,shell=True)

if __name__ == '__main__':
    nCovReport = NovelCovReport()
    soup = nCovReport.getFromURL()
    cd,pd,fd = nCovReport.extractData(soup)
    nCovReport.write2text(cd,pd,fd)
    nCovReport.trans2pdf()

    #datastructure = [ 大致数据结构
    #{'湖北':['1052','x','42','52'],'武汉':['618','x','40','45']}
    #{'香港':['5','x','0','0']}
    #{'日本':['3','x','1','0']}
    #{'韩国':['2','x','0','0']}
    #{'美国':['4','x','0','0']}
    #]
