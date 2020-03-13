#!/usr/bin/python3
import sys
import time
import logging
from bs4 import BeautifulSoup as Soup
from subprocess import call
from downloadHTML import download

logging.basicConfig(level=logging.INFO, format='%(asctime)s -%(message)s')
log = logging.getLogger(__name__)
logging.disable(logging.CRITICAL)

class NovelCronvReport():
    "2019nCov-武汉新型冠状病毒疫情报告信息采集"
    def __init__(self, province=''):
        self.name  = 'nConvReport'                                         #PDF文件名
        self.title = 'COVID-19新型冠状病毒肺炎疫情全球数据报告'            #PDF文件抬头
        self.inter = 'https://news.qq.com//zt2020/page/feiyan.htm'         #Tecent报道国内url
        self.outer = 'https://news.qq.com//zt2020/page/feiyan.htm#/global' #Tecent报道国际url

    def ExtractChinaData(self, soup):
        #提取html文件中国内各省市感染人数数据

        #中国总数据  格式A1[累计,治愈,死亡,现有] 
        divN = soup.find('div', attrs={'class':'recentNumber'})
        divs = divN.find_all('div',attrs={'class':'number'})
        nums = [div.getText().strip() for div in divs[:-2]]
        nums.insert(0,nums.pop()) #修改数据 格式A2[现有,累计,治愈,死亡] 

        #中国各省区市(含港澳台)数据 
        # 格式B
        # {  
        #   '省':['吉林','1000','2222','2000','111'],  数据B1 '省名','新增','确诊','治愈','死亡'
        #   '市':{'吉林':['618','2222','1000','111'],} 数据B2 '市名','新增','确诊','治愈','死亡'
        # }
        lstWraper = soup.find('div',attrs={'class':'listWraper'})
        tbodys    = lstWraper.find_all('tbody')

        PrvsCts = [] 
        for tbd in tbodys:
            prvAll= {'省':[],'市':{}}   #数据B 

            prvtr = tbd.find('tr',attrs={"class":"areaBox"}) 
            data  = self.getData(prvtr)
            prvAll['省'] = data[:-1]     #数据B1

            trs   = tbd.find_all('tr',attrs={"class":"city"})
            for tr in trs:
                data = self.getData(tr)
                prvAll['市'][data[0]] = data[1:-1] #数据B2

            PrvsCts.append(prvAll)     

        return nums, PrvsCts

    def ExtractForeignData(self, soup):
        #提取html文件中其他国家感染人数数据

        #外国总数据  格式C[现有,累计,治愈,死亡] 和A2保持一致
        divN = soup.find('div', attrs={'class':'recentNumber add'})
        divs = divN.find_all('div',attrs={'class':'number'})
        nums = [div.getText().strip() for div in divs]

        lstWraper = soup.find('div', attrs={'class':'listWraper'})
        tbds      = lstWraper.find_all('tbody')

        country   = {} 
        for tbd in tbds:
            data = self.getData(tbd)
            country[data[0]] = data[1:-1]

        return nums, country

    def getData(self, item):
        th  = item.find('th')     #地区/国家名
        tds = item.find_all('td') #新增，确诊，治愈，死亡，(其他)，()表示可能此项无

        #数据格式 [国家/地区名, 新增，确诊，治愈，死亡,(其他)]
        data = [th.getText().strip()]
        for td in tds:
            data.append(td.getText().strip())

        return data

    def infectedDeathNum(self, data):
        #统计各省区市的感染数及发生死亡的地区名
        ifctNum  = {} 
        district = {}

        for dic in data:
            prvd = dic['省']
            ifctNum[prvd[0]] = prvd[2]
            if '0' != prvd[-1]:
                district[prvd[0]] = prvd[-1]

        prvNum = len(district)
        if prvNum % 2:
            district['地区'] = '0'

        ifctNum  = sorted(ifctNum.items(),key=lambda v: int(v[1]),reverse=True)
        district = sorted(district.items(),key=lambda v: int(v[1]),reverse=True)
        return ifctNum, district, prvNum
        
    def serverCity(self, prvs):
        #统计感染数超百/千/的市区县名称及其感染数
        ov100, ov1000 = {}, {}
        for dic in prvs:
            ctd = dic['市']
            for k, v in ctd.items():
                if 1000 <= int(v[1]):
                    ov1000[k] = [v[1], dic['省'][0]]
                if 100 <= int(v[1]) < 1000:
                    ov100[k] = [v[1], dic['省'][0]]

        num100 = len(ov100)
        if num100 % 2:
            ov100['城市'] = ['0', '省份']
            num100 += 1

        num1000 = len(ov1000)
        if num1000 % 2:
            ov1000['城市'] = ['0', '省份']
            num1000 += 1

        ov100  = sorted(ov100.items(), key=lambda v: int(v[1][0]),reverse=True)
        ov1000 = sorted(ov1000.items(), key=lambda v: int(v[1][0]),reverse=True)

        return ov100, num100, ov1000, num1000

    def dsRate(self,data):
        #计算全球各国治愈率，死亡率
        if '0' != data[1]:  #分母不为0
            ratec = int(data[-2])*100/int(data[1])
            rated = int(data[-1])*100/int(data[1])
            if int(ratec) != 100:  #控制字符宽度
                rateStr = '%.1f%%\t%.1f%%'%(ratec,rated)
            else:
                rateStr = '%3.f%%\t%.1f%%'%(ratec,rated)
        else:
            rateStr = '----\t----'
        return rateStr

    def dRate(self,data):
        #计算中国各省治愈率，致死率
        data = data[-4:]
        if '0' != data[1]:
            if data[-2].isdigit(): #分子有效
                ratec = int(data[-2])*100/int(data[1])
                rated = int(data[-1])*100/int(data[1])
                if int(ratec) != 100:
                    rateStr = '%.1f%%\t%.1f%%'%(ratec, rated)
                else:
                    rateStr = '%3.f%%\t%.1f%%'%(ratec, rated)
            else:
                rated = int(data[-1])*100/int(data[1])
                rateStr = '------\t%.1f%%'%rated
        else:
            rateStr = '------'

        return rateStr

    def convert2pdf(self):
        #转换为pdf并发送到邮箱
        txtName  = self.name + '.txt'
        docxName = self.name + '.docx'
        pdfName  = self.name + '.pdf'

        #转成Pdf
        call('Text2docx %s 1>/dev/null 2>&1'%txtName,shell=True)
        call('Docx2pdf %s 1>/dev/null 2>&1'%docxName,shell=True)
        call('rm %s 1>/dev/null 2>&1'%docxName,shell=True)


    def allCity(self, provsD):
        #统计所有感染的城市
        ctNum , otNum = 0, {} #各市区县及境外感染数
        for dic in provsD:
            ctes = dic['市']
            ctNum += len(ctes)
            for k,v in ctes.items():
                if ('外' in k) or ('确认' in k):
                    ctNum -= 1
                if ('境外' in k):
                    otNum[dic['省'][0]] = v[1]

        ctNum += 3 #加入港澳台
        return str(len(provsD)), str(ctNum), otNum

    def initWrite(self, fobj):
        #1.初始化标题等标准信息
        timestr = time.strftime("%Y.%m.%d %H:%M:%S", time.localtime())
        fobj.write(self.title +'\n')
        fobj.write('生成时间：' + timestr +'\n')
        fobj.write('数据来源：腾讯疫情实时追踪\n')
        fobj.write('数据地址：' + self.inter + '\n')
        fobj.write('\n')

    def statGlobal(self, n1, n2, fobj):
        #2.统计全球数据
        #[现有,累计,治愈,死亡] 
        n3 = [str(int(x)+int(y)) for x,y in zip(n1,n2)] 
        fobj.write('A. COVID-19疫情报告全球统计摘要[当前值]：\n')
        fobj.write('区域\t累计\t  现有\t 治愈\t 死亡\t治愈率\t死亡率\n')
        fobj.write('中国'+'\t'+n1[1]+'    '+'\t '.join([n1[0],n1[2],n1[3],self.dsRate(n1),'\n']))
        fobj.write('外国'+'\t'+n2[1]+'    '+'\t '.join([n2[0],n2[2],n2[3],self.dsRate(n2),'\n']))
        fobj.write('全球'+'\t'+n3[1]+' '+'\t '.join([n3[0],n3[2],n3[3],self.dsRate(n3),'\n']))

        fobj.write('\n')

    def statDeathCountry(self, cD, fobj):
        #4.统计出现死亡的国家
        dcs = {}
        for k, v in cD.items():
            if '0' != v[-1]:
                dcs[k] = v[-1]

        cNum = len(dcs)
        fobj.write('B. 出现死亡国家/区域：%d个\n'%cNum)

        if cNum % 2:
            dcs['国家'] = '0'
            cNum += 1
        mid = cNum//2

        dcs = sorted(dcs.items(),key=lambda v:int(v[1]),reverse=True)
        for i in range(mid):
            p1, p2  = dcs[i], dcs[i+mid]
            ctName1 = p1[0]+':'+p1[1]
            ctName2 = p2[0]+':'+p2[1]
            fobj.write(''.join([ctName1,'\t\t',ctName2,'\n']))

        fobj.write('\n')

    def statGlobalSpecific(self, cd, fobj):
        #7.全球各国和中国详细数据
        fobj.write('C. COVID-19疫情详细数据[%d国/区域]：\n'%len(cd))
        fobj.write('国家/区域\t昨增\t累计\t治愈\t死亡\t治愈率\t死亡率\n')

        cd = sorted(cd.items(), key=lambda v: int(v[1][1]), reverse=True)
        for item in cd:
            k, v = item[0], item[1]
            drate = self.dsRate(v)
            k = k[:5] if len(k) >= 5 else k
            dlimeter = '\t\t' if len(k) < 4 else '\t'
            fobj.write(k + dlimeter + '\t'.join([v[0],v[1],v[2],v[3],drate,'\n']))

        fobj.write('\n')

    def statInportNum(self, provsD, fobj):
        #3.统计境外输入
        otNum = {} 
        for dic in provsD:
            ctes = dic['市']
            for k, v in ctes.items():
                if '境外' not in k:
                    continue
                otNum[dic['省'][0]] = v[1]

        fobj.write('D.境外输入中国：\n')
        otNum = sorted(otNum.items(), key=lambda v: int(v[1]), reverse=True)
        for item in otNum:
            k, v = item[0], item[1]
            fobj.write(''.join([k,'：',v,'\n']))

        fobj.write('\n')

    def statDeathDis(self, provsD, fobj):
        #5.统计出现死亡区域及各省区市确诊数
        fobj.write('E. 中国34个省区市确诊人数\n')

        ifNum, dDis, Provnum= self.infectedDeathNum(provsD)
        for i in range(17):
            p1, p2 = ifNum[i], ifNum[i+17]
            ctName1 = p1[0]+'：'+p1[1]
            ctName2 = p2[0]+'：'+p2[1]
            fobj.write(''.join([ctName1, '\t\t\t',ctName2,'\n']))
        fobj.write('\n')

        fobj.write('F. 出现死亡省区市：%d个\n'%Provnum)
        mid = round(Provnum/2)
        for i in range(mid):
            p1, p2 = dDis[i], dDis[i + mid]
            deli   = '\t\t' if int(p1[1]) >= 10000 else '\t\t\t'
            fobj.write(''.join([p1[0],'：',p1[1], deli, p2[0],'：',p2[1],'\n']))

        fobj.write('\n')

    def statOv100City(self, provsD, fobj):
        #6.统计确诊数上百/千/万的城市
        ov100, num100, ov1000, num1000 = self.serverCity(provsD)

        fobj.write('G. 确诊人数上千的城市/区域：%d个\n'%num1000)
        mid = round(num1000/2)
        for i in range(mid):
            p1, p2 = ov1000[i], ov1000[i + mid]
            ctName1 = p1[1][1]+'・'+p1[0]+'：'+p1[1][0]
            ctName2 = p2[1][1]+'・'+p2[0]+'：'+p2[1][0]
            fobj.write(''.join([ctName1,'\t\t\t',ctName2,'\n']))

        fobj.write('\n')
        fobj.write('H. 确诊人数上百的城市/区域：%d个\n'%num100)
        mid = round(num100/2)
        for i in range(mid):
            p1, p2 = ov100[i], ov100[i + mid]
            ctName1 = p1[1][1]+'・'+p1[0]+'：'+p1[1][0]
            ctName2 = p2[1][1]+'・'+p2[0]+'：'+p2[1][0]
            fobj.write(''.join([ctName1,'\t\t\t',ctName2,'\n']))

        fobj.write('\n')

    def statProvSpecific(self, provsD, fobj):
        #8.中国各省详细数据
        provNum, cityNum, x_ = self.allCity(provsD)
        fobj.write('I. COVID-19疫情各省区市详细数据[%s省区市，%s市区县/监狱]：\n'%(provNum, cityNum))
        fobj.write('地区\t\t昨日增\t总确诊\t治愈\t死亡\t治愈率\t死亡率\n')
        for dic in provsD:
            v   = dic['省']
            dli = '\t\t' if len(v[0]) < 4 else '\t'
            drate = self.dRate(v)
            fobj.write(v[0] + dli + '\t'.join([v[1],v[2],v[3],v[4],drate,'\n']))

            cds = dic['市']
            for k,v in cds.items():
                dli = '\t\t' if len(k) < 4 else '\t'
                drate = self.dRate(v)
                fobj.write(k + dli + '\t'.join([v[0],v[1],v[2],v[3],drate,'\n']))
            fobj.write('\n')

        fobj.write('\n')

    def newAdd(self, pd):
        #统计新增中国人数
        add = 0
        for dic in pd:
            v = dic['省']
            if v[1].isdigit():
                add += int(v[1])
            else:
                add += 0
        return [str(add)]

    def write2text(self,n1,n2,pd,cd):
        "cD:全国数据,pD:各省数据,fD:国外数据"
        with open(self.name + '.txt','w') as fobj:
            #1.初始化标题等标准信息
            self.initWrite(fobj)

            #2.统计全球数据
            self.statGlobal(n1, n2, fobj)

            #3.统计出现死亡的国家
            add = self.newAdd(pd)
            cd['中国'] = add + n1[1:]
            self.statDeathCountry(cd, fobj)

            #4.全球各国详细数据
            self.statGlobalSpecific(cd, fobj)

            #5.统计境外输入确诊数
            self.statInportNum(pd, fobj)

            #6.统计出现死亡区域及各省区市确诊数
            self.statDeathDis(pd, fobj)

            #7.统计确诊数过百的城市
            self.statOv100City(pd, fobj)

            #8.中国各省详细数据
            self.statProvSpecific(pd, fobj)

if __name__ == '__main__':
    chinaHTML, foreignHTML = download()
    NCR = NovelCronvReport()
    with open(chinaHTML) as fobj:
        html  = fobj.read()
        soup  = Soup(html,'html.parser')
        n1,pd = NCR.ExtractChinaData(soup)

    log.info(n1)
    log.info(pd[1]['省'])

    with open(foreignHTML) as fobj:
        html  = fobj.read()
        soup  = Soup(html,'html.parser')
        n2,cd = NCR.ExtractForeignData(soup)

    log.info(n2)
    log.info(cd['意大利'])

    NCR.write2text(n1,n2,pd,cd)
    NCR.convert2pdf()
