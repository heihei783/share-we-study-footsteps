from data_define import Record
import json



class FileReader:
    def read_datta(self) ->list[Record]:
        pass



class TextFileReader(FileReader):


    def __init__(self,path):
        self.path=path


    def read_data(self)->list[Record]:
        f=open(self.path,"r",encoding="UTF-8")

        recode_list:list[Record]=[]
        for line in f.readlines():
            line=line.strip()
            recode=Record(*line.split(","))
            recode_list.append(recode)
        f.close()
        return recode_list
    

class JsonFileReader(FileReader):
    def __init__(self,path):
        self.path=path
    def read_data(self)->list[Record]:
        f=open(self.path,"r",encoding="UTF-8")

        recode_list:list[Record]=[]
        for line in f.readlines():
            data_dict=json.loads(line)
            recode=Record(data_dict["date"],data_dict["order_id"],data_dict["money"],data_dict["province"])
            recode_list.append(recode)
        f.close()
        return recode_list














