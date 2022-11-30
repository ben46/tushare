# 修复接口

#### 获取k先数据
get_k_data
```commandline
获取k线数据
由于本人比较懒, 所以没有用start和end来截断dataframe
这个接口可以访问美股,港股,A股(印度股,越南股,日股等等未测试,应该也能用)
访问美股和港股需要翻墙,用的是wsj和aastock
访问港股请输入五位数代码
访问美股请输入英文代码
访问A股请输入六位数代码
```

# 新增接口

### ETF
#### 获取某个ETF K先数据
get_etf_data

### A股

#### 获取股票市值
get_market_cap

#### 获取k线数据,前复权(支持五分钟,日线等)
get_k_data_qfq

#### 获取某股票涨跌停价格
getZhangDieTing

#### 运营能力
get_operation

#### 增长数据
get_growth

#### 同比增长
get_profit_yoy

#### 获取利润表
get_profit

#### 偿债能力
get_debtpaying

#### 新浪财务指标
get_sina_caiwu_index

#### 现金流量表
get_cfst

#### 主要指标
get_mfratio

#### 新浪利润表
get_inst

#### 资产负债表(手动指定数据源sina还是qq)
get_cbsheet

#### 股本结构
get_stockstructure_data_by_code

#### 东财盈利预测
get_profit_predictdc

#### 同花顺盈利预测 
get_profit_predictths

#### 获取现金流量表
get_cashflow_data_by_code

#### 获取利润表 
get_profitstat_data_by_code

#### 获取股票分析 
get_report_data_by_code

#### 资产负债表 
get_cbsheet_by_code

----------------
### 美股和港股

#### 华尔街预测市盈率
get_wsj_hk_predict_pe

#### 华尔街港股现金流
get_wsj_hk_free_cash_flow

#### 华尔街资产负债表
get_wsj_balance_sheet

#### 华尔街港股利润表
get_wsj_hk_income_statement

#### 阿斯达克现金流表
get_aastock_cash_flow

#### 阿斯达克损益表
get_aastock_profit_loss

#### 阿斯达克资产负债表
get_aastock_balance_sheet

#### 阿斯达克回购数据
get_aastock_buyback

#### 资产负债表美股
get_cbsheet_us

#### 利润表美股
get_inst_us

#### 现金流量表美股
get_cashflow_us