# -*- coding:utf-8 -*-
__author__ = 'yueg'
import time
import math
import requests
import sys
from json import *
reload(sys)
sys.setdefaultencoding('utf-8')

# 处理及评价
class evaluate():
    def __init__(self):
        self.logPath = '../log/' + time.strftime("%Y%m%d", time.localtime()) + '.log'

    # 计算
    def coreGetPerRate(self, fileSortDic, webSortDic, twoIndustryId):
        cnt = 0
        allValue = 0
        for k in fileSortDic.keys():
            if webSortDic.has_key(k):
                value = abs(webSortDic[k] - fileSortDic[k])
                if cnt >= 2 and value > 0:
                    value -= 1
                cnt += 1
                allValue += value * value
            else:
                self.writeLog(self.logPath, 'Warning: ' + time.strftime("%Y-%m-%d %X: ", time.localtime()) + 'Not Find The Company[' + k + '] In TwoIndustryId [' + str(twoIndustryId) + ']\n')
                return 0.0
            if cnt >= 10:
                break
        if cnt == 0:
            return 0.0
        ret = 1.0 - math.sqrt(allValue * 1.0/cnt)/cnt
        return ret

    # 打印日志
    def writeLog(self, logPath, str):
        fobj = open(logPath, 'a')
        fobj.write(str)
        fobj.close()

    # 根据webapi获得的列表得到排序的公司名list
    def getWebSortList(self, inputDic):
        ret = []
        for i in range(len(inputDic)):
            max = inputDic[0]['totalScore']
            mark = 0
            for j in range(1, len(inputDic)):
                if inputDic[j]['totalScore'] > max:
                    max = inputDic[j]['totalScore']
                    mark = j
            ret.append(inputDic[mark]['companyName'])
            del inputDic[mark]
        return ret

    # 根据文件获得排序好的公司名list
    def getFileSortList(self, filePath):
        fp = open(filePath, 'r')
        str = fp.read().strip()
        fp.close()
        temp = str.split('\n')
        ret = {}
        mark = 0
        l = []
        id = 0
        for i in range(len(temp)):
            if temp[i].strip() == '':
                continue
            if temp[i].strip()[0] == '#':
                tempId = id
                id = temp[i].strip().split(':')[-1]
                if mark == 0:
                    mark = 1
                else:
                    ret[int(tempId)] = l
                    l = []
            elif temp[i].strip()[0] == '*':
                continue
            else:
                l.append(temp[i].strip())
            ret[int(id)] = l
        return ret

    # 去掉webapi获得列表中多余的公司
    def removeNoise(self, listS, listR):
        l = len(listS)
        i = 0
        while i < l:
            if listS[i] not in listR:
                del listS[i]
                l -= 1
            else:
                i += 1
        return  listS

    # list to dictionary
    # key:company, value:rank
    def convListToSortedDic(self, list):
        rank = 1
        ret = {}
        for temp in list:
            ret[temp.encode('UTF-8')] = rank
            rank += 1
        return ret

    def getTwoIndustryNameById(self, id):
        fp = open('../data/twoIndustry.txt', 'r')
        table = fp.read()
        id_name_list = table.split('\n')
        for temp in id_name_list:
            id_name = temp.split('\t')
            if len(id_name) > 1:
                twoIndustryId = int(id_name[0])
                twoIndustryName = id_name[1]
                if id == twoIndustryId:
                    return twoIndustryName
        return ''


# 调用webapi获取二级行业分类下的公司列表信息
# return json
class webApi():
    def __init__(self, twoIndustryId):
        self.ret = self.getJsonRet(twoIndustryId)

    def curl_web_query(self, url):
        r = requests.post(url)
        return r

    def getJsonRet(self, twoIndustryId):
        url_prifix = 'http://101.200.192.53:5096/'
        params = {}
        params['QueryType'] = 1
        params['data'] = {}
        params['data']['TwoIndustryId'] = int(twoIndustryId)
        k = JSONEncoder().encode(params)
        url = url_prifix + '?param=' + k
        r = self.curl_web_query(url)
        return r.text

if __name__ == '__main__':
    ev = evaluate()
    filePath = '../data/data.txt'
    fileList = ev.getFileSortList(filePath)
    ret = ''
    zeroIdList = []
    allScore = 0
    cnt = 0
    for twoIndustryId in fileList.keys():
        webJson = webApi(twoIndustryId).ret.encode('UTF-8')
        dic = JSONDecoder().decode(webJson)
        if dic['code'] == 1:
            ev.writeLog(ev.logPath, 'Warning: ' + time.strftime("%Y-%m-%d %X ", time.localtime()) + 'Not Find The Catagory, id[' + twoIndustryId + ']')
        else:
            input = dic['data']
            webList = ev.getWebSortList(input)
            webList = ev.removeNoise(webList, fileList[twoIndustryId])
            fileDic = ev.convListToSortedDic(fileList[twoIndustryId])
            webDic = ev.convListToSortedDic(webList)

            score = ev.coreGetPerRate(fileDic, webDic, twoIndustryId)
            if score == 0.0:
                zeroIdList.append(twoIndustryId)
                continue
            twoIndustryName = ev.getTwoIndustryNameById(twoIndustryId)
            allScore += score
            cnt += 1
            ret += 'id:\t' + str(twoIndustryId) + '\n'
            ret += 'catagory:\t' + twoIndustryName + '\n'
            ret += 'score:\t' + str(score) + '\n\n'
    avgScore = allScore / (0.0 + cnt)
    ret += '平均得分:\t' + str(avgScore) + '\n\n'

    ret += '二级行业中不能找到某个分类：\n'
    for temp in zeroIdList:
        twoIndustryName = ev.getTwoIndustryNameById(temp)
        ret += 'id: ' + str(temp) + '\n'
        ret += 'catagory: ' + twoIndustryName + '\n'
    rfp = open('../result/result.txt', 'w')
    rfp.write(ret)
    rfp.close()
