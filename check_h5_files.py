import pandas as pd
import os

h5_files = [
    './daily_pv_all.h5',
    './rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv_debug.h5',
    './rdagent/scenarios/qlib/experiment/factor_data_template/daily_pv_all.h5',
    './git_ignore_folder/factor_implementation_source_data_debug/daily_pv.h5',
    './git_ignore_folder/factor_implementation_source_data/daily_pv.h5',
]

def check_h5_file(path):
    print(f'\n==== 检查文件: {path} ====')
    if not os.path.exists(path):
        print('文件不存在')
        return
    try:
        with pd.HDFStore(path, mode='r') as store:
            keys = store.keys()
            print('keys:', keys)
            if '/data' not in keys:
                print('未找到 key="data"')
                return
            df = store.select('data', start=0, stop=5)
            print('前5行:')
            print(df)
            print('index type:', type(df.index))
            print('columns:', df.columns)
            # 读取全部index仅取最大最小日期
            idx = store.select('data', columns=[]).index
            dates = idx.get_level_values(0)
            print('最小日期:', dates.min())
            print('最大日期:', dates.max())
    except Exception as e:
        print('读取出错:', e)

for f in h5_files:
    check_h5_file(f) 