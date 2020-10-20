import time
import boto3
import json
from urllib.parse import urlparse
import re
class Xray():
    ''' 
    A class that will fetch dependency metrics
    '''
    def __init__(self,ACCESS_KEY,SECRET_KEY,REGION,RATE=1.0):
        self.client = boto3.client('xray',region_name=REGION,aws_access_key_id=ACCESS_KEY,aws_secret_access_key=SECRET_KEY)
        self.rate = RATE
    
    def __removeDomain(self,url):
        res = urlparse(url)
        return res.netloc,res.path
    def __getTraceIds(self,start,end):
        nxtToken=''
        GET = {}
        PUT = {}
        POST = {}
        DELETE = {}
        RESP = {"GET":GET,"PUT":PUT,"POST":POST,"DELETE":DELETE}
        while 1:
            response = self.client.get_trace_summaries(
                StartTime=start,
                EndTime=end,
                Sampling=True,
                TimeRangeType='TraceId',
                SamplingStrategy={
                    'Name': 'PartialScan',
                    'Value': self.rate
                },
                NextToken=nxtToken
            )
            for item in response['TraceSummaries']:
                if 'Http' in item and item['Http']['HttpStatus']>=200 and item['Http']['HttpStatus']<300:
                    _,url = self.__removeDomain(item['Http']['HttpURL'])
                    url = re.sub(r'/\d+',"/{id}",url)
                    method = item['Http']['HttpMethod']
                    # print (method+' : '+url)
                    if "ping" in url or "error" in url or "healthcheck" in url:
                        continue
                    else:
                        store = RESP[method]
                        if url in store:
                            store[url].append(item['Id']) 
                            RESP[method] = store
                        else:
                            store[url] = [item['Id']]
                    
                    
            if 'NextToken' in response:
                nxtToken=response['NextToken']
            else: 
                break
        return RESP                
    def __getFullTrace(self,traceIds):
        nxtToken=''
        GET = {}
        PUT = {}
        POST = {}
        DELETE = {}
        RESP = {"GET":GET,"PUT":PUT,"POST":POST,"DELETE":DELETE}
        while(1):
            response = self.client.batch_get_traces(
                TraceIds=traceIds
            )
            for item in response['Traces']:
                for segString in item['Segments']:
                    seg = json.loads(segString['Document'])
                    if 'http' in seg:
                        service,url = self.__removeDomain(seg['http']['request']['url'])
                        url = re.sub(r'/\d+',"/{id}",url)
                        method = seg['http']['request']['method']
                        store = RESP[method]
                        if url in store:
                            continue
                        else:
                            store[url] = service
                            RESP[method]=store
                    
            if 'NextToken' in response:
                nxtToken = response['NextToken']
            else:
                break

        return RESP
        

    def structureData(self,fixedRate=0,start=None,end=None):
        if fixedRate<1:
            fixedRate=5
        if start==None :
            end = time.time()
            start = end-3600
        source = self.__getTraceIds(start,end)
        RESULT =[]
        for method in source:
            for url in source[method]:
                resp = self.__getFullTrace(source[method][url][0:fixedRate])
                sService=''
                dest = []
                for reqMet in resp:
                    for item in resp[reqMet]:
                        if method != reqMet or item != url:
                            dest.append({"METHOD":reqMet,"SERVICE":resp[reqMet][item],"PATH":item})
                        else:
                            sService = resp[reqMet][item]
                RESULT.append({"SERVICE":sService,"METHOD":method,"PATH":url,"DESTINATION":dest})
        return RESULT

