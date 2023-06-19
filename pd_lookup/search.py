import os
import re
from collections import OrderedDict

path = os.path.abspath(__file__)
dir_path = os.path.dirname(path)

class PersonalDevice(object):
    
    def __init__(self):
        self.pdmap = OrderedDict()
        self.cache = {}

        sorted_files=sorted(os.scandir("{}/txt".format(dir_path)), key=lambda e: e.name)
        for filename in sorted_files:
            if filename.is_file(): 
                with open(filename.path) as file:
                    self.pdmap[filename.name] = [line.rstrip() for line in file]

    def search(self,*args) -> dict:
        for txt in args: 
            if txt in self.cache: 
                return self.cache[txt]
            for key in self.pdmap:
                for value in self.pdmap[key]:
                    value = value.lower()
                    if re.search(value,txt,re.IGNORECASE):
                        importance,devicetype=key.split('_')
                        self.cache[txt]=[devicetype,value]
                        return self.cache[txt]
        return ["",""]


    def getPDMap(self) -> OrderedDict:
        return self.pdmap
