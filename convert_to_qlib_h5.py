import pandas as pd

df = pd.read_csv("all_daily_from_tushare.csv")
df['datetime'] = pd.to_datetime(df['trade_date'], format='%Y%m%d')
df['instrument'] = df['ts_code']
df = df.rename(columns={
    'open': 'open',
    'close': 'close',
    'high': 'high',
    'low': 'low',
    'vol': 'volume'
})
df = df[['datetime', 'instrument', 'open', 'close', 'high', 'low', 'volume']]
df = df.set_index(['datetime', 'instrument']).sort_index()
df.to_hdf("daily_pv_all.h5", key="data")
print("已生成 daily_pv_all.h5") 