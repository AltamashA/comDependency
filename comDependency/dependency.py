from service import converter
from service import xray
from service import excel
import time
import json



if __name__ =='__main__':
    xrayClient = xray.Xray('','','us-east-1')
    xlxsClient = converter.Convert()
    payload = xrayClient.structureData()
    excelClient = excel.excel()
    excelClient.saveSpecial(payload)