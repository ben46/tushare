# 横跨三个股票市场(A股,美股,港股)的股票量化的工具箱
本项目是在tushare基础上改的, 原链接(https://github.com/waditu/tushare/blob/master/README.md)
由于tushare作者大佬名声鹊起之后, 被通联大数据纳入麾下, tushare这个库就停止了更新
TuShare是实现对股票/期货等金融数据从数据采集、清洗加工 到 数据存储过程的工具，满足金融量化分析师和学习数据分析的人在数据获取方面的需求，它的特点是数据覆盖范围广，接口调用简单,响应快速。
并且支持美股, 港股, A股等一系列数据. 具体功能模块可以在页面内搜索关键字.

**如果有大佬看中小弟, 小弟正在找工作, 请联系我ben02060846@qq.com**


# 运行环境
```commandline
python 3.6.8
```

# 依赖库
```commandline
requests>=2.0.0
lxml>=3.8.0
simplejson>=3.16.0
bs4>=0.0.1
beautfulsoup4>=4.5.1
```

# 可能需要的依赖
由于本人时间有限, 没空看代码哪些依赖是需要的
列出可能需要的依赖库, 如果无法运行, 请安装以下依赖
```commandline
numpy=1.19.5
pandas=0.23.3
Pillow=8.4.0
```

# 如何安装
```
git clone https://github.com/ben46/tushare.git
cd tushare
python install_tushare.py install
```
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