import tushare as ts
import pandas as pd
import time

token = "6f8cc83f22acc925e65adf42cc5427a79f4954ca72eb66d844ce2d00"
ts.set_token(token)
pro = ts.pro_api()

stocks = pro.stock_basic(exchange='', list_status='L', fields='ts_code')

all_data = []
for i, ts_code in enumerate(stocks['ts_code']):
    print(f"正在获取: {ts_code} ({i+1}/{len(stocks)})")
    try:
        df = pro.daily(ts_code=ts_code, start_date='19900101', end_date='20250721',
            fields='ts_code,trade_date,open,high,low,close,pre_close,change,pct_chg,vol,amount')
        if not df.empty:
            all_data.append(df)
        time.sleep(0.3)
    except Exception as e:
        print(f"获取 {ts_code} 失败: {e}")

if all_data:
    df_all = pd.concat(all_data, ignore_index=True)
    df_all.to_csv("all_daily_from_tushare.csv", index=False)
    print("已保存为 all_daily_from_tushare.csv")
else:
    print("未获取到任何数据！") 