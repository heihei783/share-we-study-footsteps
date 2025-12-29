from file_define import FileReader,TextFileReader,JsonFileReader
from data_define import Record
from pyecharts.charts import Bar
from pyecharts.options import *
from pyecharts.globals import ThemeType


text_file_reader = TextFileReader(r".\2011年1月销售数据.txt")
json_file_reader=JsonFileReader(r".\2011年2月销售数据JSON.txt")
list1:list[Record]=text_file_reader.read_data()
list2:list[Record]=json_file_reader.read_data()


all_data:list[Record]=list1+list2

data_dict={}
for record in all_data:
    try:
        data_dict[record.date]+=record.money
    except:
        data_dict[record.date]=record.money


bar = Bar(init_opts=InitOpts(theme=ThemeType.LIGHT))
bar.add_xaxis(list(data_dict.keys()))
bar.add_yaxis("销售额",list(data_dict.values()),label_opts=LabelOpts(is_show=False))
bar.set_global_opts(
    title_opts=TitleOpts(title="每日销售额")

)

bar.render("每日销售额柱状图.html")












