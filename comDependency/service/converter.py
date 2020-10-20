from json_excel_converter import Converter 
from json_excel_converter.xlsx import Writer
from datetime import datetime
import os

class Convert():
    def __init__(self):
        self.conv = Converter()
        self.dir = datetime.now().strftime("%m-%d-%Y")
    
    def __makeDir(self):
        if not os.path.exists(self.dir):
            os.makedirs(self.dir)
    def convert(self,filename,payload):
        self.__makeDir()
        self.conv.convert(payload,Writer(file=filename))
