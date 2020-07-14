# 导入futu-api
import futu as ft
import pandas as pd
from datetime import date,timedelta

oldData=pd.read_csv('ProccessedData\hsi future 1M combined from youtube futu.csv',index_col=0)
lastupdate=date.fromisoformat(oldData.iloc[-1,0])
# oneDay=timedelta(days=1)
today=date.today()

quote_ctx = ft.OpenQuoteContext(host="127.0.0.1", port=11111)

# 上下文控制
quote_ctx.start()              # 开启异步数据接收
quote_ctx.set_handler(ft.TickerHandlerBase())  # 设置用于异步处理数据的回调对象(可派生支持自定义)

#HSI HK.800000
#HSI Future HK.999010
# ret, data, page_req_key = quote_ctx.request_history_kline('HK.999010', start='2020-05-21', end=str(today), ktype=ft.KLType.K_1M, autype=ft.AuType.HFQ, max_count=None)
# print(data)
# # data.to_csv('RawData/futu_hsiFuture_1M.csv')

futu_olddata=pd.read_csv('RawData\\futu_hsiFuture_1M.csv',index_col=0) #取得舊資料
futu_olddata=futu_olddata.drop(futu_olddata.iloc[-181:].index) #刪除最後一天00:00到03:00的資料
futu_newdata = futu_olddata.append(data,ignore_index = True) #結合OLD and NEW
futu_newdata.to_csv('RawData\\new_futu_hsiFuture_1M.csv') #寫入檔案

oldData=oldData.drop(oldData[oldData['<Date>']==str(lastupdate)].index)
data = data[['time_key','open','high','low','close']] #去除不需要的資料
dateAndTime_data = pd.DataFrame(data.time_key.str.split(' ',1).tolist(),columns=['<Date>','<Time>']) #分開time_key
data = dateAndTime_data.join(data).drop(['time_key'],axis=1) #刪除time_key
data = data.rename(columns={'open':'<Open>', 'high':'<High>', 'low':'<Low>', 'close':'<Close>'}) #改columns名稱
newData = oldData.append(data,ignore_index = True) #結合OLD and NEW
newData.to_csv('ProccessedData/hsi future 1M combined from youtube futu.csv') #寫入檔案



# 停止异步数据接收
quote_ctx.stop()
# 关闭对象
quote_ctx.close()