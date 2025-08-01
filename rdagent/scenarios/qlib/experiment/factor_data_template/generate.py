import qlib

qlib.init(provider_uri="~/.qlib/qlib_data/cn_data")

from qlib.data import D

instruments = D.instruments()
fields = ["$open", "$close", "$high", "$low", "$volume", "$factor"]

# 生成完整数据
data = D.features(instruments, fields, freq="day").swaplevel().sort_index().loc["2008-12-29":].sort_index()
data.to_hdf("./daily_pv_all.h5", key="data")

# 修复：先获取2018-2019年的数据，然后取前100只股票
debug_data = D.features(instruments, fields, start_time="2018-01-01", end_time="2019-12-31", freq="day").swaplevel().sort_index()

# 从debug_data中取前100只股票，而不是从完整数据集中取
available_instruments = debug_data.reset_index()["instrument"].unique()[:100]
debug_data = debug_data.swaplevel().loc[available_instruments].swaplevel().sort_index()

debug_data.to_hdf("./daily_pv_debug.h5", key="data")
