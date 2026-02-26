---
title: 공모주 최소청약단위 크롤링 (균등배정 case)
date: 2023-07-02
tags:
  - 삽질
  - 공모주
  - 크롤링
  - Python
  - OpenDart
  - 케이뱅크
category:
  - 실무경험
  - 공모주
---

ex) 공모주의 경우 최소청약금액 중요

### 문제점

연합인포맥스에서 해당 데이터를 제공해주지 않음(심지어 나머지 데이터들도 수기로 관리하고 있다는 자백을 받음)

### 해결 point

금융감독원 전자공시시스템 오픈api 활용

공모주는 지분증권이기 때문에 해당 공시자료를 스캔하면 확인 가능

## Try

### 대상 데이터

케이뱅크 공모주 DB 내부에 저장되어 있는 공모주 데이터(2021년도분 부터 싹다)

### 실험 방법

python elemTree를 활용한 크롤링

### 포인트 및 가정

- 증권사별로 청약단위가 같다(이건 솔직히 맞음)
- 연합인포맥스가 제대로된 공시자료를 줬다(일단 가정)

### 내용

오픈api 활용 금감원 공시자료 다운 + 압축해제 + 인코딩 스크립트

```python
import csv
import zipfile
import requests
import time
from loguru import logger
crtfc_key = "bfb1272f4109ed5e959ff0b82b40bb08291ffb45"

class IpoInfo:
    def __init__(self, itmsCdNbr, stckKorNm, dmdFrcsStartDt, dmdFrcsEndDt, sbscStartDt, sbscClsgDt,
                 pymDt, drbcDt, stckLstnDt, lwenScdlPbofAmt, tppoScdlPbofAmt, cnfmPbofAmt, pbofStckCnt,
                 sbscRvlrRt, rprsSpicComNm, jointSpicComNm, rbpeComNm, fssRcipNbr, stckFaceAmt,
                 aissGnrlStckCnt, aissPrtyStckCnt, nmnRrtProxyInstNm, dmdFrcsRvlrRt, oblgDfpnAplctRate):
        self.itmsCdNbr = itmsCdNbr
        self.stckKorNm = stckKorNm
        self.dmdFrcsStartDt = dmdFrcsStartDt
        self.dmdFrcsEndDt = dmdFrcsEndDt
        self.sbscStartDt = sbscStartDt
        self.sbscClsgDt = sbscClsgDt
        self.pymDt = pymDt
        self.drbcDt = drbcDt
        self.stckLstnDt = stckLstnDt
        self.lwenScdlPbofAmt = lwenScdlPbofAmt
        self.tppoScdlPbofAmt = tppoScdlPbofAmt
        self.cnfmPbofAmt = cnfmPbofAmt
        self.pbofStckCnt = pbofStckCnt
        self.sbscRvlrRt = sbscRvlrRt
        self.rprsSpicComNm = rprsSpicComNm
        self.jointSpicComNm = jointSpicComNm
        self.rbpeComNm = rbpeComNm
        self.fssRcipNbr = fssRcipNbr
        self.stckFaceAmt = stckFaceAmt
        self.aissGnrlStckCnt = aissGnrlStckCnt
        self.aissPrtyStckCnt = aissPrtyStckCnt
        self.nmnRrtProxyInstNm = nmnRrtProxyInstNm
        self.dmdFrcsRvlrRt = dmdFrcsRvlrRt
        self.oblgDfpnAplctRate = oblgDfpnAplctRate
    def __str__(self):
        return f"ITMS_CD_NBR: {self.itmsCdNbr}, STCK_KOR_NM: {self.stckKorNm}, DMD_FRCS_START_DT: {self.dmdFrcsStartDt}, DMD_FRCS_END_DT: {self.dmdFrcsEndDt}, SBSC_START_DT: {self.sbscStartDt}, SBSC_CLSG_DT: {self.sbscClsgDt}, PYM_DT: {self.pymDt}, DRBC_DT: {self.drbcDt}, STCK_LSTN_DT: {self.stckLstnDt}, LWEN_SCDL_PBOF_AMT: {self.lwenScdlPbofAmt}, TPPO_SCDL_PBOF_AMT: {self.tppoScdlPbofAmt}, CNFM_PBOF_AMT: {self.cnfmPbofAmt}, PBOF_STCK_CNT: {self.pbofStckCnt}, SBSC_RVLR_RT: {self.sbscRvlrRt}, RPRS_SPIC_COM_NM: {self.rprsSpicComNm}, JOINT_SPIC_COM_NM: {self.jointSpicComNm}, RBPE_COM_NM: {self.rbpeComNm}, FSS_RCIP_NBR: {self.fssRcipNbr}, STCK_FACE_AMT: {self.stckFaceAmt}, AISS_GNRL_STCK_CNT: {self.aissGnrlStckCnt}, AISS_PRTY_STCK_CNT: {self.aissPrtyStckCnt}, NMN_RRT_PROXY_INST_NM: {self.nmnRrtProxyInstNm}, DMD_FRCS_RVLR_RT: {self.dmdFrcsRvlrRt}, OBLG_DFPN_APLCT_RATE: {self.oblgDfpnAplctRate}"

def read_ipo_data(file_path):
    ipo_objects = []
    with open(file_path, 'r', newline='',encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            ipo_object = IpoInfo(
                row['ITMS_CD_NBR'], row['STCK_KOR_NM'], row['DMD_FRCS_START_DT'], row['DMD_FRCS_END_DT'],
                row['SBSC_START_DT'], row['SBSC_CLSG_DT'], row['PYM_DT'], row['DRBC_DT'],
                row['STCK_LSTN_DT'], row['LWEN_SCDL_PBOF_AMT'], row['TPPO_SCDL_PBOF_AMT'],
                row['CNFM_PBOF_AMT'], row['PBOF_STCK_CNT'], row['SBSC_RVLR_RT'], row['RPRS_SPIC_COM_NM'],
                row['JOINT_SPIC_COM_NM'], row['RBPE_COM_NM'], row['FSS_RCIP_NBR'], row['STCK_FACE_AMT'],
                row['AISS_GNRL_STCK_CNT'], row['AISS_PRTY_STCK_CNT'], row['NMN_RRT_PROXY_INST_NM'],
                row['DMD_FRCS_RVLR_RT'], row['OBLG_DFPN_APLCT_RATE']
            )
            ipo_objects.append(ipo_object)
    return ipo_objects

def getFileData(rcept_no):
    endPoint = "https://opendart.fss.or.kr/api/document.xml" \
                +"?crtfc_key="+ crtfc_key + "&rcept_no=" + rcept_no
    logger.info(endPoint)
    response = requests.get(endPoint)
    try:
        with open("./reportZips/"+rcept_no+".zip",'wb') as f:
            f.write(response.content)
    except:
        logger.error(rcept_no +" when download zipfile")

def unzipFileData(rcept_no):
    zipFilePath = "./reportZips/"+rcept_no+".zip"
    targetXmlFilePath = "./reports"
    try:
        with zipfile.ZipFile(zipFilePath,'r') as f:
            f.extractall(targetXmlFilePath)
    except:
        logger.error(rcept_no + " when extract from zipfile")

def convertXmlData(rcept_no):
    targetXmlFilePath = "./reports"
    try:
        with open(targetXmlFilePath,'r',encoding='euc-kr') as f:
            lines = f.readlines()
        with open(targetXmlFilePath,'w',encoding='utf-8') as f:
            f.writelines(f)
    except:
        logger.error(rcept_no + " when convert euc-kr -> utf-8 from zipfile")

if __name__ == "__main__":
    data = read_ipo_data('./ipo_dat.csv')
    idx = 0
    for ele in data:
        if ele.fssRcipNbr == None or len(ele.fssRcipNbr.strip()) == 0:
            logger.error(ele.stckKorNm)
            continue
        logger.info("금감원접수번호 "+ ele.fssRcipNbr + " 청약시작일" + ele.sbscStartDt)
        getFileData(ele.fssRcipNbr)
        unzipFileData(ele.fssRcipNbr)
        convertXmlData(ele.fssRcipNbr)
        time.sleep(1)
```

각각의 파일 파싱하여 최소청약단위 산출하는 스크립트

```python
import xml.etree.ElementTree as elemTree
import re
from bs4 import BeautifulSoup
from loguru import logger
import os

def parseFromXml(xmlName):
    targetXmlFilePath = f"./reports/{xmlName}"
    codedXmlFile = ""
    try:
        with open(targetXmlFilePath, 'r', encoding='utf-8') as f:
            codedXmlFile = '\n'.join(f.readlines())
    except:
        with open(targetXmlFilePath, 'r', encoding='euc-kr') as f:
            codedXmlFile = '\n'.join(f.readlines())

    ele = BeautifulSoup(codedXmlFile,'lxml')
    for pTag in ele.findAll('p'):
        pTag.replace_with(pTag.text)

    trLi = ele.findAll('tr')
    pattern = re.compile(r'.*청약단위.*')
    pattern2 = re.compile(r'.*')
    pattern3 = re.compile(r'.*【.*')
    pattern4 = re.compile(r'.*\[.*')
    flag = False
    resArr = []
    for idx in range(len(trLi)):
        curTr = trLi[idx]

        if len(curTr.findAll('th')) != 0 \
                and (curTr.findAll('th')[0].text.strip() == '청약주식수' or curTr.findAll('th')[0].text.strip() == '청약증권수' )\
                and curTr.findAll('th')[1].text.strip() == '청약단위':
            try:
                tmpArr = []
                tmpArr.append(f'{ele.find("title").text:20}')
                first = trLi[idx + 1].findAll('td')[0].text.strip().replace('\n', ' ').replace(' ','')
                tmpArr.append(f'{first:30}')
                second = trLi[idx+1].findAll('td')[1].text.strip().replace('\n',' ').replace(' ','')
                tmpArr.append(f'{second:30}')
                return tmpArr
            except:
                logger.error(curTr)
                logger.error(curTr.findAll('td'))
                logger.error(trLi[idx+1])
        if len(curTr.findAll('td')) != 0 and curTr.findAll('td')[0].text.strip() == '청약주식수' and curTr.findAll('td')[1].text.strip() == '청약단위':
            try:
                tmpArr = []
                tmpArr.append(f'{ele.find("title").text:20}')
                first = trLi[idx + 1].findAll('td')[0].text.strip().replace('\n', ' ').replace(' ','')
                tmpArr.append(f'{first:30}')
                second = trLi[idx + 1].findAll('td')[1].text.strip().replace('\n', ' ').replace(' ','')
                tmpArr.append(f'{second:30}')
                return tmpArr
            except:
                logger.error(curTr)
                logger.error(trLi[idx+1])
    resArr.append(f'{ele.find("title").text:20}')
    return resArr

if __name__ == "__main__":
    folderPath = './reports'
    fileNames = [f for f in os.listdir(folderPath) if os.path.isfile(os.path.join(folderPath, f))]
    for fileName in fileNames:
        try:
            logger.info(fileName + " " + '@'.join(parseFromXml(fileName)))
        except UnicodeDecodeError as e:
            logger.error(fileName +"  "+ e.reason)
        except IndexError as e:
            logger.error(fileName +"  " + str(e))
```

### 결과

<details>
<summary>길어서 접음</summary>

```
/Users/kimminseok/PycharmProjects/openDartDocumentParser/venv/bin/python /Users/kimminseok/PycharmProjects/openDartDocumentParser/parser.py
2023-10-19 15:54:52.894 | INFO     | __main__:<module>:78 - 20231011000391.xml 정 정 신 고 (보고)                  @10주이상~100주이하                  @10주
2023-10-19 15:54:52.986 | INFO     | __main__:<module>:78 - 20210430001176.xml 증권발행조건확정                      @10주이상~100주이하                  @10주
2023-10-19 15:54:53.064 | INFO     | __main__:<module>:78 - 20210521000157.xml 증권발행조건확정                      @100주이상~500주이하                 @50주
2023-10-19 15:54:53.284 | INFO     | __main__:<module>:78 - 20211215000062.xml 증권발행조건확정                      @10주이상~100주이하                  @10주
2023-10-19 15:54:53.351 | INFO     | __main__:<module>:78 - 20230828000365.xml 증권발행조건확정                      @100주이하                        @10주
2023-10-19 15:54:53.408 | INFO     | __main__:<module>:78 - 20230728000264.xml 증권발행조건확정                      @100주이상~1,000주이하               @100주
2023-10-19 15:54:53.433 | INFO     | __main__:<module>:78 - 20210730000186.xml 증권발행조건확정
2023-10-19 15:54:54.443 | INFO     | __main__:<module>:78 - 20231017000143.xml 정 정 신 고 (보고)                  @10주이상~100주이하                  @10주
2023-10-19 15:54:54.541 | INFO     | __main__:<module>:78 - 20210310000574.xml 증권발행조건확정                      @10주이상~100주이하                  @10주
2023-10-19 15:54:54.818 | INFO     | __main__:<module>:78 - 20210326000420.xml 증권발행조건확정
2023-10-19 15:54:55.015 | INFO     | __main__:<module>:78 - 20221122000123.xml 증권발행조건확정                      @10주이상~100주이하                  @10주
2023-10-19 15:54:55.077 | INFO     | __main__:<module>:78 - 20210723000054.xml 증권발행조건확정
2023-10-19 15:54:55.289 | INFO     | __main__:<module>:78 - 20220613000179.xml 증권발행조건확정
2023-10-19 15:54:55.535 | INFO     | __main__:<module>:78 - 20220718000098.xml 증권발행조건확정
2023-10-19 15:54:55.692 | INFO     | __main__:<module>:78 - 20230605000256.xml 증권발행조건확정                      @20주이상~100주이하
```

</details>

### 예외 처리

이유 : 청약 하시는분들 대부분 큰 금액을 넣기보다는 소액으로 치킨값을 버시는 분들이 많음

그러므로 의무확약비율 & 높은 경쟁률을 찾을듯

문제는 경쟁률이 높으면 균등배정으로 가져갈 수 밖에 없음(천만원 넣어야 1주 비례배정 이런식으로 되어버림)

그러므로 최소납입금액을 안내해줘야 할 듯

중간에 빈 로그 - 잘못준것 or 기재정정된 내용만 있는 보고서 → 다른 보고서로 대체하는 로직 필요, 예컨데 기재정정 이전 보고서를 다시 받아 파싱 시도

log.error - 교보생명의 경우 포맷이 약간 다름 - 문제 없음(그냥 예외 처리)

### 최소균등배정 물량 산출 로직

다음과 같은 케이스가 있음

- `10주이상~100주이하 / 10주`
- `100주이하 / 10주`
- `20주이상~100주이하 / 10주`

### 그 외의 예외사항

20230323001109 한화리츠 (지분증권 상장이 아니라 집합투자증권 발행 후 상장이라 양식이 살짝 다름)

### 예외처리 프로세스

1. 기재정정되어서 발행조건이 확정된 공시의 경우 최소청약건수를 공시하지 않음(기재정정 전 공시자료에 공시되어 있으므로) → 따라서 최초의 증권신고서를 가지고 판단하는 것이 맞음
   - 기재정정 보고서 테이블에 적재되어있음 - 이력테이블(TB_SCK_PBOF_INFO_X)에서 해당 보고서 최신 버전으로 수정하는 이력 확인 완료. 따라서 최초 적재되는 보고서를 파싱하면 문제없음
   - ⇒ 최소청약물량 10주
   - 기재정정되었을 때 해당 최소청약건수가 변경되는 경우? - 일단 찾아본 케이스에서는 없었음(그런식으로 일을 하면 애초에 안되기도 함). 최소청약건수의 경우 대체로 공모가에 영향을 많이 받기 때문에(공모가가 높으면 청약물량이 낮아지는 느낌) 공모가가 확정된 시점에 크롤링을 수행하면 문제되지 않음
2. 연합인포맥스에서 잘못된 공시 접수번호를 주는 경우
   - 생각도 하기 싫다
   - 만약에 그런 경우 크롤링 실패 → 금감원에 등록된 해당 기업 고유번호를 활용하여 증권신고서를 다시 가져와서 크롤링 시도하면 됨
   - ⇒ 최소청약물량 10주
3. 발행조건이 확정되지 않은 경우
   - 공모가 확정 시점까지 보류
   - ⇒ 최소청약물량 20주
