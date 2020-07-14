import pandas as pd
import pybacktest
import matplotlib
import matplotlib.pyplot as plt
import talib as ta

df = pd.read_csv("^HSI.csv")
df.index=pd.to_datetime(df['Date'])
df=df.dropna()
df=df[['Open','High','Low','Close']]
df.columns=["O","H","L","C"]
ohlc = df.copy()
close = df['C']

logic = {'O'  : 'first',
         'H'  : 'max',
         'L'   : 'min',
         'C' : 'last'}
offset = pd.offsets.timedelta(days=-6)
weekdata =df.resample('W', loffset=offset).apply(logic)
weekclose=weekdata['C']

top_Long_filter = 93
bot_Long_filter = 170
week_macd_filter = -100
Long_loss_value = 4

No_August = False
No_November = False

Week_fastLength = 30
Week_slowLength = 57
Week_signalLength = 4

rsi_entry_length = 405
rsi_exit_length = 362
rsi_entry_filter = 50
rsi_exit_filter = 52

fastLength = 30
slowLength = 57
signalLength = 4

exit_fastLength = 30
exit_slowLength = 34
exit_signalLength = 4

Macd, Macdsignal, Macdhist = ta.MACD(close, fastperiod=fastLength, slowperiod=slowLength, signalperiod=signalLength)
exit_Macd, exit_Macdsignal, exit_Macdhist = ta.MACD(close, fastperiod=exit_fastLength, slowperiod=exit_slowLength, signalperiod=exit_signalLength)
Week_Macd, Week_Macdsignal, Week_Macdhist = ta.MACD(weekclose, fastperiod=Week_fastLength, slowperiod=Week_slowLength, signalperiod=Week_signalLength)

entry_Rsi = ta.RSI(close,rsi_entry_length)
exit_Rsi = ta.RSI(close,rsi_exit_length)

Week_Macdhist_resampled=Week_Macdhist.resample('B').ffill().shift(5)
weekbool=(Week_Macdhist_resampled>=week_macd_filter)
df['W']=weekbool
weekbool=df['W']
sell= (exit_Macd<exit_Macdsignal) & (exit_Macd.shift()>=exit_Macdsignal.shift()) & (exit_Macd>=top_Long_filter) & (exit_Rsi>rsi_exit_filter)
buy= (Macd>Macdsignal) & (Macd.shift()<=Macdsignal.shift()) & (Macd<=-bot_Long_filter) & (entry_Rsi<=rsi_entry_filter) & weekbool

bt = pybacktest.Backtest(locals(), 'test1')
bt.summary()

matplotlib.rcParams['figure.figsize'] = (15.0, 8.0)
bt.plot_equity()
try:
    bt.plot_trades()
    
except ValueError:
        pass
# finally:
#     plt.legend(loc='upper right')



