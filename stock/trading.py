# -*- coding:utf-8 -*- 
"""
交易数据接口 
Created on 2014/07/31
@author: Jimmy Liu
@contact: jimmysoa@sina.cn
------------------------
modified at 2022-10-30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
from __future__ import division

import datetime
import time
import json
import lxml.html
from lxml import etree
import pandas as pd
import numpy as np
from tushare.stock import cons as ct
import re
# from pandas.compat import StringIO
from io import StringIO
from tushare.util import dateu as du
import os

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request
import requests


def _code_to_symbol(code):
    """
        生成symbol代码标志
    """
    if code in ct.INDEX_LABELS:
        return ct.INDEX_LIST[code]
    else:
        if re.compile(u"[a-zA-Z]+").search(code, 0) is not None:
            return 'us%s' % code
        if len(code) == 5:
            return 'hk%s' % code
        elif len(code) != 6:
            return ''
        else:
            return 'sh%s' % code if code[:1] in ['5', '6', '9'] else 'sz%s' % code

def set_use_cache(use_cache):
    ct.USE_CACHE = use_cache
    return ct.USE_CACHE

def set_current_year_season(year, season):
    ct.CURRENT_YEAR = year
    ct.CURRENT_SEASON = season

def get_hist_data(code=None, start=None, end=None,
                  ktype='D', retry_count=3,
                  pause=0.001):
    """
        获取个股历史交易记录
    Parameters
    ------
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取到API所提供的最早日期数据
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取到最近一个交易日数据
      ktype：string
                  数据类型，D=日k线 W=周 M=月 5=5分钟 15=15分钟 30=30分钟 60=60分钟，默认为D
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数 
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
    return
    -------
      DataFrame
          属性:日期 ，开盘价， 最高价， 收盘价， 最低价， 成交量， 价格变动 ，涨跌幅，5日均价，10日均价，20日均价，5日均量，10日均量，20日均量，换手率
    """
    symbol = _code_to_symbol(code)
    url = ''
    if ktype.upper() in ct.K_LABELS:
        url = ct.DAY_PRICE_URL % (ct.P_TYPE['http'], ct.DOMAINS['ifeng'],
                                  ct.K_TYPE[ktype.upper()], symbol)
    elif ktype in ct.K_MIN_LABELS:
        url = ct.DAY_PRICE_MIN_URL % (ct.P_TYPE['http'], ct.DOMAINS['ifeng'],
                                      symbol, ktype)
    else:
        raise TypeError('ktype input error.')

    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(url)
            lines = urlopen(request, timeout=10).read()
            if len(lines) < 15:  # no data
                return None
        except Exception as e:
            print(e)
        else:
            js = json.loads(lines.decode('utf-8') if ct.PY3 else lines)
            cols = []
            if (code in ct.INDEX_LABELS) & (ktype.upper() in ct.K_LABELS):
                cols = ct.INX_DAY_PRICE_COLUMNS
            else:
                cols = ct.DAY_PRICE_COLUMNS
            if len(js['record'][0]) == 14:
                cols = ct.INX_DAY_PRICE_COLUMNS
            df = pd.DataFrame(js['record'], columns=cols)
            if ktype.upper() in ['D', 'W', 'M']:
                df = df.applymap(lambda x: x.replace(u',', u''))
                df[df == ''] = 0
            for col in cols[1:]:
                df[col] = df[col].astype(float)
            if start is not None:
                df = df[df.date >= start]
            if end is not None:
                df = df[df.date <= end]
            if (code in ct.INDEX_LABELS) & (ktype in ct.K_MIN_LABELS):
                df = df.drop('turnover', axis=1)
            df = df.set_index('date')
            df = df.sort_index(ascending=False)
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_tick_data(code=None, date=None, retry_count=3, pause=0.001):
    """
        获取分笔数据
    Parameters
    ------
        code:string
                  股票代码 e.g. 600848
        date:string
                  日期 format：YYYY-MM-DD
        retry_count : int, 默认 3
                  如遇网络等问题重复执行的次数
        pause : int, 默认 0
                 重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
     return
     -------
        DataFrame 当日所有股票交易数据(DataFrame)
              属性:成交时间、成交价格、价格变动，成交手、成交金额(元)，买卖类型
    """
    if code is None or len(code) != 6 or date is None:
        return None
    symbol = _code_to_symbol(code)
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            re = Request(ct.TICK_PRICE_URL % (ct.P_TYPE['http'], ct.DOMAINS['sf'], ct.PAGES['dl'],
                                              date, symbol))
            lines = urlopen(re, timeout=10).read()
            lines = lines.decode('GBK')
            if len(lines) < 20:
                return None
            df = pd.read_table(StringIO(lines), names=ct.TICK_COLUMNS,
                               skiprows=[0])
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_sina_dd(code=None, date=None, vol=400, retry_count=3, pause=0.001):
    """
        获取sina大单数据
    Parameters
    ------
        code:string
                  股票代码 e.g. 600848
        date:string
                  日期 format：YYYY-MM-DD
        retry_count : int, 默认 3
                  如遇网络等问题重复执行的次数
        pause : int, 默认 0
                 重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
     return
     -------
        DataFrame 当日所有股票交易数据(DataFrame)
              属性:股票代码    股票名称    交易时间    价格    成交量    前一笔价格    类型（买、卖、中性盘）
    """
    if code is None or len(code) != 6 or date is None:
        return None
    symbol = _code_to_symbol(code)
    vol = vol * 100
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            re = Request(ct.SINA_DD % (ct.P_TYPE['http'], ct.DOMAINS['vsf'], ct.PAGES['sinadd'],
                                       symbol, vol, date))
            lines = urlopen(re, timeout=10).read()
            lines = lines.decode('GBK')
            if len(lines) < 100:
                return None
            df = pd.read_csv(StringIO(lines), names=ct.SINA_DD_COLS,
                             skiprows=[0])
            if df is not None:
                df['code'] = df['code'].map(lambda x: x[2:])
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_today_ticks(code=None, retry_count=3, pause=0.001):
    """
        获取当日分笔明细数据
    Parameters
    ------
        code:string
                  股票代码 e.g. 600848
        retry_count : int, 默认 3
                  如遇网络等问题重复执行的次数
        pause : int, 默认 0
                 重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
     return
     -------
        DataFrame 当日所有股票交易数据(DataFrame)
              属性:成交时间、成交价格、价格变动，成交手、成交金额(元)，买卖类型
    """
    if code is None or len(code) != 6:
        return None
    symbol = _code_to_symbol(code)
    date = du.today()
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(ct.TODAY_TICKS_PAGE_URL % (ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                                         ct.PAGES['jv'], date,
                                                         symbol))
            data_str = urlopen(request, timeout=10).read()
            data_str = data_str.decode('GBK')
            data_str = data_str[1:-1]
            data_str = eval(data_str, type('Dummy', (dict,),
                                           dict(__getitem__=lambda s, n: n))())
            data_str = json.dumps(data_str)
            data_str = json.loads(data_str)
            pages = len(data_str['detailPages'])
            data = pd.DataFrame()
            ct._write_head()
            for pNo in range(1, pages + 1):
                data = data.append(_today_ticks(symbol, date, pNo,
                                                retry_count, pause), ignore_index=True)
        except Exception as er:
            print(str(er))
        else:
            return data
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def _today_ticks(symbol, tdate, pageNo, retry_count, pause):
    ct._write_console()
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            html = lxml.html.parse(ct.TODAY_TICKS_URL % (ct.P_TYPE['http'],
                                                         ct.DOMAINS['vsf'], ct.PAGES['t_ticks'],
                                                         symbol, tdate, pageNo
                                                         ))
            res = html.xpath('//table[@id=\"datatbl\"]/tbody/tr')
            if ct.PY3:
                sarr = [etree.tostring(node).decode('utf-8') for node in res]
            else:
                sarr = [etree.tostring(node) for node in res]
            sarr = ''.join(sarr)
            sarr = '<table>%s</table>' % sarr
            sarr = sarr.replace('--', '0')
            df = pd.read_html(StringIO(sarr), parse_dates=False)[0]
            df.columns = ct.TODAY_TICK_COLUMNS
            df['pchange'] = df['pchange'].map(lambda x: x.replace('%', ''))
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_realtime_quotes(symbols=None):
    """
        获取实时交易数据 getting real time quotes data
       用于跟踪交易情况（本次执行的结果-上一次执行的数据）
    Parameters
    ------
        symbols : string, array-like object (list, tuple, Series).

    return
    -------
        DataFrame 实时交易数据
              属性:0：name，股票名字
            1：open，今日开盘价
            2：pre_close，昨日收盘价
            3：price，当前价格
            4：high，今日最高价
            5：low，今日最低价
            6：bid，竞买价，即“买一”报价
            7：ask，竞卖价，即“卖一”报价
            8：volumn，成交量 maybe you need do volumn/100
            9：amount，成交金额（元 CNY）
            10：b1_v，委买一（笔数 bid volume）
            11：b1_p，委买一（价格 bid price）
            12：b2_v，“买二”
            13：b2_p，“买二”
            14：b3_v，“买三”
            15：b3_p，“买三”
            16：b4_v，“买四”
            17：b4_p，“买四”
            18：b5_v，“买五”
            19：b5_p，“买五”
            20：a1_v，委卖一（笔数 ask volume）
            21：a1_p，委卖一（价格 ask price）
            ...
            30：date，日期；
            31：time，时间；
    """
    symbols_list = ''
    if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple) or isinstance(symbols,
                                                                                                         pd.Series):
        for code in symbols:
            symbols_list += _code_to_symbol(code) + ','
    else:
        symbols_list = _code_to_symbol(symbols)

    symbols_list = symbols_list[:-1] if len(symbols_list) > 8 else symbols_list
    request = Request(ct.LIVE_DATA_URL % (ct.P_TYPE['http'], ct.DOMAINS['sinahq'],
                                          _random(), symbols_list))
    text = urlopen(request, timeout=10).read()
    text = text.decode('GBK')
    reg = re.compile(r'\="(.*?)\";')
    data = reg.findall(text)
    regSym = re.compile(r'(?:sh|sz)(.*?)\=')
    syms = regSym.findall(text)
    data_list = []
    syms_list = []
    for index, row in enumerate(data):
        if len(row) > 1:
            data_list.append([astr for astr in row.split(',')])
            syms_list.append(syms[index])
    if len(syms_list) == 0:
        return None
    df = pd.DataFrame(data_list, columns=ct.LIVE_DATA_COLS)
    df = df.drop('s', axis=1)
    df['code'] = syms_list
    ls = [cls for cls in df.columns if '_v' in cls]
    for txt in ls:
        df[txt] = df[txt].map(lambda x: x[:-2])
    return df


def get_h_data(code, start=None, end=None, autype='qfq',
               index=False, retry_count=3, pause=0.001, drop_factor=True):
    '''
    获取历史复权数据
    Parameters
    ------
      code:string
                  股票代码 e.g. 600848
      start:string
                  开始日期 format：YYYY-MM-DD 为空时取当前日期
      end:string
                  结束日期 format：YYYY-MM-DD 为空时取去年今日
      autype:string
                  复权类型，qfq-前复权 hfq-后复权 None-不复权，默认为qfq
      retry_count : int, 默认 3
                 如遇网络等问题重复执行的次数
      pause : int, 默认 0
                重复请求数据过程中暂停的秒数，防止请求间隔时间太短出现的问题
      drop_factor : bool, 默认 True
                是否移除复权因子，在分析过程中可能复权因子意义不大，但是如需要先储存到数据库之后再分析的话，有该项目会更加灵活
    return
    -------
      DataFrame
          date 交易日期 (index)
          open 开盘价
          high  最高价
          close 收盘价
          low 最低价
          volume 成交量
          amount 成交金额
    '''

    start = du.today_last_year() if start is None else start
    end = du.today() if end is None else end
    qs = du.get_quarts(start, end)
    qt = qs[0]
    ct._write_head()
    data = _parse_fq_data(_get_index_url(index, code, qt), index,
                          retry_count, pause)
    if data is None:
        data = pd.DataFrame()
    if len(qs) > 1:
        for d in range(1, len(qs)):
            qt = qs[d]
            ct._write_console()
            df = _parse_fq_data(_get_index_url(index, code, qt), index,
                                retry_count, pause)
            if df is None:  # 可能df为空，退出循环
                break
            else:
                data = data.append(df, ignore_index=True)
    if len(data) == 0 or len(data[(data.date >= start) & (data.date <= end)]) == 0:
        return None
    data = data.drop_duplicates('date')
    if index:
        data = data[(data.date >= start) & (data.date <= end)]
        data = data.set_index('date')
        data = data.sort_index(ascending=False)
        return data
    if autype == 'hfq':
        if drop_factor:
            data = data.drop('factor', axis=1)
        data = data[(data.date >= start) & (data.date <= end)]
        for label in ['open', 'high', 'close', 'low']:
            data[label] = data[label].map(ct.FORMAT)
            data[label] = data[label].astype(float)
        data = data.set_index('date')
        data = data.sort_index(ascending=False)
        return data
    else:
        if autype == 'qfq':
            if drop_factor:
                data = data.drop('factor', axis=1)
            df = _parase_fq_factor(code, start, end)
            df = df.drop_duplicates('date')
            df = df.sort('date', ascending=False)
            firstDate = data.head(1)['date']
            frow = df[df.date == firstDate[0]]
            rt = get_realtime_quotes(code)
            if rt is None:
                return None
            if ((float(rt['high']) == 0) & (float(rt['low']) == 0)):
                preClose = float(rt['pre_close'])
            else:
                if du.is_holiday(du.today()):
                    preClose = float(rt['price'])
                else:
                    if (du.get_hour() > 9) & (du.get_hour() < 18):
                        preClose = float(rt['pre_close'])
                    else:
                        preClose = float(rt['price'])

            rate = float(frow['factor']) / preClose
            data = data[(data.date >= start) & (data.date <= end)]
            for label in ['open', 'high', 'low', 'close']:
                data[label] = data[label] / rate
                data[label] = data[label].map(ct.FORMAT)
                data[label] = data[label].astype(float)
            data = data.set_index('date')
            data = data.sort_index(ascending=False)
            return data
        else:
            for label in ['open', 'high', 'close', 'low']:
                data[label] = data[label] / data['factor']
            if drop_factor:
                data = data.drop('factor', axis=1)
            data = data[(data.date >= start) & (data.date <= end)]
            for label in ['open', 'high', 'close', 'low']:
                data[label] = data[label].map(ct.FORMAT)
            data = data.set_index('date')
            data = data.sort_index(ascending=False)
            data = data.astype(float)
            return data


def _parase_fq_factor(code, start, end):
    symbol = _code_to_symbol(code)
    request = Request(ct.HIST_FQ_FACTOR_URL % (ct.P_TYPE['http'],
                                               ct.DOMAINS['vsf'], symbol))
    text = urlopen(request, timeout=10).read()
    text = text[1:len(text) - 1]
    text = text.decode('utf-8') if ct.PY3 else text
    text = text.replace('{_', '{"')
    text = text.replace('total', '"total"')
    text = text.replace('data', '"data"')
    text = text.replace(':"', '":"')
    text = text.replace('",_', '","')
    text = text.replace('_', '-')
    text = json.loads(text)
    df = pd.DataFrame({'date': list(text['data'].keys()), 'factor': list(text['data'].values())})
    df['date'] = df['date'].map(_fun_except)  # for null case
    if df['date'].dtypes == np.object:
        df['date'] = df['date'].astype(np.datetime64)
    df = df.drop_duplicates('date')
    df['factor'] = df['factor'].astype(float)
    return df


def _fun_except(x):
    if len(x) > 10:
        return x[-10:]
    else:
        return x


def _parse_fq_data(url, index, retry_count, pause):
    for _ in range(retry_count):
        time.sleep(pause)
        try:
            request = Request(url)
            text = urlopen(request, timeout=10).read()
            text = text.decode('GBK')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath('//table[@id=\"FundHoldSharesTable\"]')
            if ct.PY3:
                sarr = [etree.tostring(node).decode('utf-8') for node in res]
            else:
                sarr = [etree.tostring(node) for node in res]
            sarr = ''.join(sarr)
            if sarr == '':
                return None
            df = pd.read_html(sarr, skiprows=[0, 1])[0]
            if len(df) == 0:
                return pd.DataFrame()
            if index:
                df.columns = ct.HIST_FQ_COLS[0:7]
            else:
                df.columns = ct.HIST_FQ_COLS
            if df['date'].dtypes == np.object:
                df['date'] = df['date'].astype(np.datetime64)
            df = df.drop_duplicates('date')
        except ValueError as e:
            # 时间较早，已经读不到数据
            return None
        except Exception as e:
            print(e)
        else:
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)


def get_index():
    """
    获取大盘指数行情
    return
    -------
      DataFrame
          code:指数代码
          name:指数名称
          change:涨跌幅
          open:开盘价
          preclose:昨日收盘价
          close:收盘价
          high:最高价
          low:最低价
          volume:成交量(手)
          amount:成交金额（亿元）
    """
    request = Request(ct.INDEX_HQ_URL % (ct.P_TYPE['http'],
                                         ct.DOMAINS['sinahq']))
    text = urlopen(request, timeout=10).read()
    text = text.decode('GBK')
    text = text.replace('var hq_str_sh', '').replace('var hq_str_sz', '')
    text = text.replace('";', '').replace('"', '').replace('=', ',')
    text = '%s%s' % (ct.INDEX_HEADER, text)
    df = pd.read_csv(StringIO(text), sep=',', thousands=',')
    df['change'] = (df['close'] / df['preclose'] - 1) * 100
    df['amount'] = df['amount'] / 100000000
    df['change'] = df['change'].map(ct.FORMAT)
    df['amount'] = df['amount'].map(ct.FORMAT4)
    df = df[ct.INDEX_COLS]
    df['code'] = df['code'].map(lambda x: str(x).zfill(6))
    df['change'] = df['change'].astype(float)
    df['amount'] = df['amount'].astype(float)
    return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def _get_index_url(index, code, qt):
    if index:
        url = ct.HIST_INDEX_URL % (ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                   code, qt[0], qt[1])
    else:
        url = ct.HIST_FQ_URL % (ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                code, qt[0], qt[1])
    return url

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def _get_cwfx(url, key='czzb', retry_count=3, pause=5):
    for _ in range(retry_count):
        try:
            print(sys._getframe().f_code.co_name, url)
            request = Request(url)
            lines = urlopen(request, timeout=10).read()
            if len(lines) < 100:  # no data
                return None
            else:
                lines = lines.decode('utf-8') if ct.PY3 else lines
                lines = lines.replace('--', '')
                lines = lines.split('=')[1]
                js = json.loads(lines[:-1])
                df = pd.DataFrame(js['data'][key])
                for col in df.columns:
                    try:
                        df[col] = [x.replace(',', '') for x in df[col]]
                        df[col] = df[col].astype(float)
                    except:
                        pass
                df.index = list(df['bgrq'])
                return df
        except Exception as e:
            print(sys._getframe().f_code.co_name, url)
            print(e)
            time.sleep(pause)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def _get_cbsheet(url, retry_count=3, pause=5):
    for _ in range(retry_count):
        try:
            print(sys._getframe().f_code.co_name, url)
            request = Request(url)
            text = urlopen(request, timeout=10).read()
            text = text.decode('gb2312')
            text = text.replace('--', '')
            text = text.replace('万元', '')
            text = text.replace('万', '')
            text = text.replace(',', '')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath("//table[@class=\"list list_d\"]")
            df = pd.read_html(etree.tostring(res[0]))[0]
            df = df.transpose()
            df0 = df[1:]
            df0 = df0[df0.columns[1:]]
            df0.columns = list(df.iloc[0][1:])
            df0.index = list(df[0][1:])
            df0 = df0[pd.notnull(df0.index)]
            for col in df0.columns:
                try:
                    df0[col] = [x.replace(',', '') for x in df0[col]]
                    df0[col] = df0[col].astype(float)
                except:
                    pass
            df0 = df0.fillna(0)
            return df0
        except Exception as e:
            print(sys._getframe().f_code.co_name, url)
            print(e)
            time.sleep(pause)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def __parse_sina_table(url, retry_count=1, pause=5, table_name='ProfitStatementNewTable0', update=False):
    for _ in range(retry_count):
        try:
            print(sys._getframe().f_code.co_name, url)
            __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
            current_year = ct.CURRENT_YEAR
            current_season = ct.CURRENT_SEASON
            if os.path.exists(__cache_file_path) and ct.USE_CACHE and not update:
                print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
                df0 = pd.read_csv(__cache_file_path, index_col=0)
                def __cal_df0(df0):
                    cols = []
                    for col in df0.columns:
                        cols.append(unicode(col))
                    df0.columns = cols
                    return df0

                if table_name != 'ProfitStatementNewTable0':
                    return __cal_df0(df0)
                else:
                    # print df0.index[0].split('-')
                    # print current_year, current_season
                    if df0.index[0].split('-')[0] != current_year:
                        return __cal_df0(df0)
                    elif df0.index[0].split('-')[1] == current_season:
                        return __cal_df0(df0)

            request = Request(url)
            text = urlopen(request, timeout=10).read()
            text = text.decode('gb2312')
            text = text.replace('--', '')
            text = text.replace(',', '')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath("//table[@id=\"%s\"]" % table_name)
            df = pd.read_html(etree.tostring(res[0]))[0]
            df = df.transpose()
            df0 = df[1:]
            df0 = df0[df0.columns[1:]]
            df0.columns = list(df.iloc[0][1:])
            df0.index = list(df[0][1:])
            df0 = df0[pd.notnull(df0.index)]
            for col in df0.columns:
                try:
                    df0[col] = [x.replace(',', '') for x in df0[col]]
                    df0[col] = df0[col].astype(float)
                except Exception as e:
                    # print(e)
                    pass
            df0 = df0.fillna(0)
            print('save to cache', __cache_file_path)
            df0.to_csv(__cache_file_path)
            time.sleep(3)
            return df0
        except Exception as e:
            print(sys._getframe().f_code.co_name, url)
            print(e)
            time.sleep(pause)
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def __convert_billion_dataframe(df):
    # 把亿万转换为数字,方便计算
    d = {'亿': 10 ** 8, '万': 10 ** 4}
    for col in df.columns:
        # dataframe中有的类型是object,转换为string
        df[col] = df[col].astype('|S')  # which will by default set the length to the max len it encounters

    arr1 = []
    for i in range(df.shape[0]):
        arr0 = []
        for col in df.columns:
            pos0 = df.iloc[i][col].find('亿')
            pos1 = df.iloc[i][col].find('万')
            if pos0 > 0:
                mult = 10 ** 8
                num = df.iloc[i][col][:pos0]
            elif pos1 > 0:
                mult = 10 ** 4
                num = df.iloc[i][col][:pos1]
            else:
                mult = 1
                num = df.iloc[i][col]
            arr0.append(float(num) * mult)
        arr1.append(arr0)
    df = pd.DataFrame(data=arr1, columns=df.columns)

    return df
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def __parse_sina_table_us(url, retry_count=1, pause=5, table_name='ProfitStatementNewTable0'):
    for _ in range(retry_count):
        # try:
            print(sys._getframe().f_code.co_name, url)
            __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))

            # if not os.path.exists(__cache_file_path):
            #     # 如果不存在缓存, 那就是获取不到的股票了,或者是新股
            #     return None

            if os.path.exists(__cache_file_path) and ct.USE_CACHE:
                print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
                df0 = pd.read_csv(__cache_file_path, index_col=0)
                def __cal_df0(df0):
                    cols = []
                    for col in df0.columns:
                        cols.append(unicode(col))
                    df0.columns = cols
                    return df0
                df0 = __convert_billion_dataframe(df0)
                return __cal_df0(df0)

            request = Request(url)
            text = urlopen(request, timeout=10).read()
            text = text.decode('gb2312')
            # html = lxml.html.parse(StringIO(text))
            # res0 = html.xpath("//table")
            # df000 = pd.read_html(etree.tostring(res0[0]))[0]
            # print df000
            # exit()

            text = text.replace('--', '')
            text = text.replace(',', '')
            html = lxml.html.parse(StringIO(text))

            res = html.xpath("//table[@class=\"%s\"]" % table_name)
            df = pd.read_html(etree.tostring(res[1]))[0]
            df = df.transpose()
            df0 = df[1:]
            df0 = df0[df0.columns[1:]]
            df0.columns = list(df.iloc[0][1:])
            df0.index = list(df[0][1:])
            df0 = df0[pd.notnull(df0.index)]
            for col in df0.columns:
                try:
                    df0[col] = [x.replace(',', '') for x in df0[col]]
                    df0[col] = df0[col].astype(float)
                except Exception as e:
                    # print(e)
                    pass
            df0 = df0.fillna(0)
            print('save to cache', __cache_file_path)
            df0.to_csv(__cache_file_path)
            time.sleep(10)
            df0 = __convert_billion_dataframe(df0)
            return df0
        # except Exception, e:
        #     print sys._getframe().f_code.co_name, url
        #     print e
        #     time.sleep(pause)
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_cbsheet(code, year, sina=True, update=False):
    '''
    资产负债表
    负债合计
    '''
    if sina:
        url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_BalanceSheet/stockid/%s/ctrl/%s/displaytype/4.phtml' % (
            code, str(year))
        return __parse_sina_table(url, table_name='BalanceSheetNewTable0', update=update)
    url = 'http://stock.finance.qq.com/corp1/cbsheet.php?zqdm=%s&type=%d' % (code, year)
    return _get_cbsheet(url)
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_cbsheet_us(code):
    '''
    资产负债表
    负债合计
    '''
    url = 'https://quotes.sina.com.cn/usstock/hq/balance.php?s=%s&t=annual' % (code)
    return __parse_sina_table_us(url, table_name='data_tbl os_tbl')
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_inst_us(code):
    '''
    资产负债表
    负债合计
    '''
    url = 'https://quotes.sina.com.cn/usstock/hq/income.php?s=%s&t=annual' % (code)
    return __parse_sina_table_us(url, table_name='data_tbl os_tbl')
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_cashflow_us(code):
    '''
    资产负债表
    负债合计
    '''
    url = 'https://quotes.sina.com.cn/usstock/hq/cash.php?s=%s&t=annual' % (code)
    return __parse_sina_table_us(url, table_name='data_tbl os_tbl')
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_aastock_profit_loss(code, period, is_update = False):
    url = 'http://www.aastocks.com/en/stocks/analysis/company-fundamental/profit-loss?symbol=%s&period=%d' \
                      % (code, period)
    print(sys._getframe().f_code.co_name, url)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    if not is_update and os.path.exists(__cache_file_path) and os.path.exists(__cache_file_path + '2') and ct.USE_CACHE:
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df = pd.read_csv(__cache_file_path, index_col=0)
        df2 = pd.read_csv(__cache_file_path + '2', index_col=
                          0)
        return df, df2

    for _ in range(3):
        try:
            text = urlopen(Request(url.encode('utf-8')), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    try:
        sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list"]')[0])
        df = pd.read_html(sarr)[0]
        sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list2"]')[0])
        df2 = pd.read_html(sarr)[0]
        df.to_csv(__cache_file_path)
        df2.to_csv(__cache_file_path + '2')
        return df, df2
    except:
        return None, None

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_aastock_buyback(code, is_update=False):
    url = 'http://www.aastocks.com/en/stocks/analysis/company-fundamental/securities-buyback?symbol=%s' \
                      % (code)
    print(sys._getframe().f_code.co_name, url)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    if not is_update and os.path.exists(__cache_file_path) and ct.USE_CACHE:
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df = pd.read_csv(__cache_file_path, index_col=0)
        return df

    for _ in range(3):
        try:
            text = urlopen(Request(url.encode('utf-8')), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    try:
        sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@class="cnhk-cf tblM s4 s5 mar15T"]')[0])
        df = pd.read_html(sarr)[0]
        df.to_csv(__cache_file_path)
        return df
    except:
        return None

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_aastock_balance_sheet(code, period):
    print('get_aastock_balance_sheet')
    url = 'http://www.aastocks.com/en/stocks/analysis/company-fundamental/balance-sheet?symbol=%s&period=%d' \
                      % (code, period)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    print('是否使用缓存: ', ct.USE_CACHE)
    if os.path.exists(__cache_file_path) and ct.USE_CACHE:
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df0 = pd.read_csv(__cache_file_path, index_col=0)
        return df0
    else:
        print('正在从网络获取')

    for _ in range(3):
        try:
            text = urlopen(Request(url.encode('utf-8')), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list"]')[0])
    df = pd.read_html(sarr)[0]
    df.to_csv(__cache_file_path)
    sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list2"]')[0])
    df2 = pd.read_html(sarr)[0]
    return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_aastock_cash_flow(code, period):
    url = 'http://www.aastocks.com/en/stocks/analysis/company-fundamental/cash-flow?symbol=%s&period=%d' \
                      % (code, period)
    print(sys._getframe().f_code.co_name, url)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    if os.path.exists(__cache_file_path) and ct.USE_CACHE:
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df0 = pd.read_csv(__cache_file_path, index_col=0)
        return df0

    for _ in range(3):
        try:
            text = urlopen(Request(url.encode('utf-8')), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list"]')[0])
    df = pd.read_html(sarr)[0]
    df.to_csv(__cache_file_path)
    # sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//table[@id="cnhk-list2"]')[0])
    # df2 = pd.read_html(sarr)[0]
    return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_wsj_hk_income_statement(code, cf_type='quarter', market='HK'):
    if market == 'in':
        url = 'https://quotes.wsj.com/in/xbom/%s/financials/%s/income-statement' % (code, cf_type)
    else:
        url = 'https://quotes.wsj.com/HK/%s/financials/%s/income-statement' % (code[1:], cf_type)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    # if os.path.exists(__cache_file_path) and (ct.USE_CACHE or cf_type == 'annual'):
    if os.path.exists(__cache_file_path) and (ct.USE_CACHE):
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df0 = pd.read_csv(__cache_file_path, index_col=0)
        return df0
    print(sys._getframe().f_code.co_name, url)
    for _ in range(3):
        try:
            text = urlopen(Request(url), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    html = lxml.html.parse(StringIO(text))
    res = html.xpath('//table[@class="cr_dataTable"]')
    sarr = etree.tostring(res[0])
    df = pd.read_html(sarr)[0]
    df.to_csv(__cache_file_path)
    return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_wsj_balance_sheet(code, cf_type='annual', market='hk'):
    if market == 'in':
        url = 'https://quotes.wsj.com/in/xbom/%s/financials/%s/balance-sheet' % (code, cf_type)
    elif market == 'hk':
        url = 'https://quotes.wsj.com/HK/%s/financials/%s/balance-sheet' % (code[1:], cf_type)
    elif market == 'us':
        url = 'https://quotes.wsj.com/%s/financials/%s/balance-sheet' % (code, cf_type)
    elif market == 'a':
        if code.find('6') == 0:
            url = 'https://quotes.wsj.com/CN/XSHG/%s/financials/%s/balance-sheet' % (code, cf_type)
        else:
            url = 'https://quotes.wsj.com/CN/XSHE/%s/financials/%s/balance-sheet' % (code, cf_type)
    print(sys._getframe().f_code.co_name, url)
    __cache_file_path = '%s%s' % (ct.CACHE_DIR, url.replace('/', ''))
    if os.path.exists(__cache_file_path) and os.path.exists(__cache_file_path+'1') and (ct.USE_CACHE or cf_type == 'annual'):
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df0 = pd.read_csv(__cache_file_path, index_col=0)
        df1 = pd.read_csv(__cache_file_path + '1', index_col=0)
        return df0, df1


    for _ in range(3):
        try:
            text = urlopen(Request(url), timeout=60).read()
            break
        except Exception as e:
            print(e)
            time.sleep(60)
    html = lxml.html.parse(StringIO(text))
    res = html.xpath('//table[@class="cr_dataTable"]')

    df = pd.read_html(etree.tostring(res[0]))[0]
    df.to_csv(__cache_file_path)

    df1 = pd.read_html(etree.tostring(res[1]))[0]
    df1.to_csv(__cache_file_path + '1')

    return df, df1

import sys
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_wsj_hk_free_cash_flow(code, cf_type='annual', market='hk'):
    if market == 'hk':
        url = 'https://quotes.wsj.com/HK/%s/financials/%s/cash-flow' % (code[1:], cf_type)
    elif market == 'us':
        url = 'https://quotes.wsj.com/%s/financials/%s/cash-flow' % (code, cf_type)
    elif market == 'in':
        url = 'https://quotes.wsj.com/in/xbom/%s/financials/%s/cash-flow' % (code, cf_type)
    elif market == 'a':
        if code.find('6') == 0:
            url = 'https://quotes.wsj.com/CN/XSHG/%s/financials/%s/cash-flow' % (code, cf_type)
        else:
            url = 'https://quotes.wsj.com/CN/XSHE/%s/financials/%s/cash-flow' % (code, cf_type)
    print(sys._getframe().f_code.co_name, url)
    __cache_file_path = '%s%s2' % (ct.CACHE_DIR, url.replace('/', ''))
    if os.path.exists(__cache_file_path) and os.path.exists(__cache_file_path + '1') and os.path.exists(
            __cache_file_path + '2') and (ct.USE_CACHE or cf_type == 'annual'):
        print(sys._getframe().f_code.co_name, '正在使用缓存', __cache_file_path)
        df0 = pd.read_csv(__cache_file_path, index_col=0)
        df1 = pd.read_csv(__cache_file_path+'1', index_col=0)
        df2 = pd.read_csv(__cache_file_path+'2', index_col=0)
        return df0, df1, df2
    for _ in range(3):
        try:
            text = urlopen(Request(url), timeout=60).read()
            break
        except Exception as e:
            print (e, '获取自由现金流失败')
            time.sleep(60)
    html = lxml.html.parse(StringIO(text))
    res = html.xpath('//table[@class="cr_dataTable"]')

    df = pd.read_html(etree.tostring(res[0]))[0]
    df.to_csv(__cache_file_path)

    df1 = pd.read_html(etree.tostring(res[1]))[0]
    df1.to_csv(__cache_file_path + '1')

    df2 = pd.read_html(etree.tostring(res[2]))[0]
    df2.to_csv(__cache_file_path + '2')

    return df, df1, df2

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_wsj_hk_predict_pe(code):
    try:
        wsj_pe_url = 'https://quotes.wsj.com/HK/XHKG/%s/research-ratings' % code[1:]
        text = urlopen(Request(wsj_pe_url.encode('utf-8')), timeout=60).read()
        sarr = etree.tostring(lxml.html.parse(StringIO(text)).xpath('//*[@id="rr_module_yearly_estimates"]/table[@class="cr_dataTable crTable-trends"]/tbody/tr[@class="firstRow"]/td[@class="valueCell"]')[0])
        earning_per_share = float(sarr.split('</sup>')[1].split('<')[0])
        price = float(lxml.html.parse(StringIO(text)).xpath('//*[@id="quote_val"]')[0].text)
        return price * 1.0 / earning_per_share
    except Exception as e:
        print(e)
        return 0
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_inst(code, year, sina=True, ttm=False):
    '''
    公司利润表
    营业收入, 归属于母公司的净利润, 营业外收入,
    营业外支出, 投资收益,
    其中:对联营企业和合营企业的投资收益,
    资产减值损失, 公允价值变动收益
    '''
    # print 'get_inst'
    if sina:
        url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/%s/ctrl/%d/displaytype/4.phtml' % (
            code, year)
        if ttm:
            url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/%s/ctrl/part/displaytype/4.phtml' % (code)
        df = __parse_sina_table(url, table_name='ProfitStatementNewTable0')
        return df
    else:
        url = 'http://stock.finance.qq.com/corp1/inst.php?zqdm=%s&type=%d' % (code, year)
        return _get_cbsheet(url)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_mfratio(code, year=2016):
    '''
       u'基本每股收益',                      u'稀释每股收益',   u'每股收益加权平均',   u'每股收益摊薄(扣除非经常性损益后)',
       u'每股收益加权平均(扣除非经常性损益后)', u'每股净资产',     u'每股净资产(调整后)', u'每股经营活动产生的现金流量净额',
       u'净资产收益率摊薄',                  u'净资产收益率加权', u'主营业务收入',      u'主营业务利润',
       u'营业利润',                         u'投资收益',        u'营业外收支净额',    u'利润总额',
       u'净利润',                           u'净利润(扣除非经常性损益后)',
       u'经营活动产生的现金流量净额',          u'现金及现金等价物净增加额',
       u'流动资产',                         u'流动负债',        u'总资产', u'股东权益不含少数股东权益'
    '''
    if sina:
        url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/%s/ctrl/%d/displaytype/4.phtml' % (
        code, year)
        return __parse_sina_table(url, table_name='ProfitStatementNewTable0')
    url = 'http://stock.finance.qq.com/corp1/mfratio.php?zqdm=%s&type=%d' % (code, year)
    return _get_cbsheet(url)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_cfst(code, year=2016, sina=True):
    '''
    现金流量
    '''
    if sina:
        url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_CashFlow/stockid/%s/ctrl/%d/displaytype/4.phtml' % (
            code, year)
        return __parse_sina_table(url, table_name='ProfitStatementNewTable0')
    url = 'http://stock.finance.qq.com/corp1/cfst.php?zqdm=%s&type=%d' % (code, year)
    return _get_cbsheet(url)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_sina_caiwu_index(code, year):
    url = 'http://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/%s/ctrl/%d/displaytype/4.phtml' % (
        code, year)
    return __parse_sina_table(url, table_name='BalanceSheetNewTable0')

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_debtpaying(code, year=2016, years=0, index=False):
    symbol = ct.INDEX_SYMBOL[code] if index else _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/czzb/%s/%d' % (symbol, year)
    return _get_cwfx(url, 'czzb')

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_profit(code, year=2016, years=0, index=False):
    '''
    u'bgrq', u'cbfylrl',
    报告日期  成本费用利润率(%)
    u'fjcxsybl',         u'jlrkc',
    非经常性损益比率(%)    扣除非经常性损益后的净利润(元)
    u'jzcsyljq',         u'sxfyl',
    净资产收益率(加权)(%)  三项费用率(%)
    u'xsjll',        u'xsmll',       u'xsqlr',
    销售净利率(%)  	 销售毛利率(%)    息税前利润(元)
    u'xsqlrl',       u'yylrl',       u'zzclrl'
    息税前利润率(%)    营业利润率(%)   总资产利润率 (%)
    '''
    symbol = ct.INDEX_SYMBOL[code] if index else _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/ylnl/%s/%d' % (symbol, year)
    return _get_cwfx(url, 'ylnl')

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_profit_yoy(code, year=2016):
    '''
    扣非净利润同比
    '''
    symbol = _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/ylnl/%s/%d' % (symbol, year)
    df_0 = _get_cwfx(url, 'ylnl')
    df_0['jlrkc_yoy'] = np.nan
    print(df_0)
    url = 'http://comdata.finance.gtimg.cn/data/ylnl/%s/%d' % (symbol, year - 1)
    df_1 = _get_cwfx(url, 'ylnl')
    for idx, row in df_0.iterrows():
        date = str(year - 1) + '-' + row['bgrq'][5:]
        rets = df_1[df_1['bgrq'] == date]
        print(rets)
        if rets.shape[0] > 0:
            try:
                val = (row['jlrkc'] / float(rets.iloc[0]['jlrkc']) - 1) * 100
                df_0.set_value(idx, 'jlrkc_yoy', val)
            except Exception as e:
                print(e)
    return df_0

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_operation(code, year=2016):
    symbol = _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/yynl/%s/%d' % (symbol, year)
    df = _get_cwfx(url, 'yynl')
    df.columns = ['报告日期', '存货资产构成率',
                  '存货周转率', '存货周转天数',
                  '股东权益周转率', '固定资产周转率',
                  '流动资产周转率', '流动资产周转天数',
                  '应收账款周转率', '应收账款周转天数',
                  '总资产周转率', '总资产周转天数'
                  ]
    return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_growth(code, year=2016, years=0, index=False):
    '''
    mgsy 每股收益增长率(%)	16.15	14.93	3.93	20.23
    mgxj 每股现金流增长率(%)	--	-153.05	--	-146.28
    zysr 主营收入增长率(%)	22.98	33.58	8.10	31.33
    yylr 营业利润增长率(%)	17.81	32.60	2.95	15.45
    lrze 利润总额增长率(%)	16.13	33.86	3.96	15.29
    jlr 净利润增长率(%)	16.02	15.08	4.15	20.46
    xsqlr 息税前利润增长率(%)	20.87	31.14	1.85	15.49
    zzc 总资产增长率(%)
    '''
    symbol = ct.INDEX_SYMBOL[code] if index else _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/cznl/%s/%d' % (symbol, year)
    return _get_cwfx(url, 'cznl')

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_djcw(code, year=2016, years=0, index=False):
    symbol = ct.INDEX_SYMBOL[code] if index else _code_to_symbol(code)
    url = 'http://comdata.finance.gtimg.cn/data/djcw/%s/%d' % (symbol, year)
    return _get_cwfx(url, 'djcw')


from datetime import date


def _get_k_data_us(code, ktype='D', start=''):
    '''
        :param symbol:
        :return: D, W, M
        '''
    s = requests.session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "s=8h12kjdra3; bid=9f8e558960ffc59db81ccd585ad314ed_is5nt7yr; __utma=1.883182649.1471534174.1471534174.1472446021.2; __utmc=1; __utmz=1.1471534174.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); xq_a_token=0c491a0cbcaaa3d60047e8fe70136358b85b3114; xq_r_token=a372978b648bc0c63bec1ac4e4278052716d9a5b; Hm_lvt_1db88642e346389874251b5a1eded6e3=1471421838,1471936805,1472028850,1472189875; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1472551749",
        "Host": "xueqiu.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36"
    }

    r = s.get(
        'https://xueqiu.com/S/%s' % code,
        headers=headers,
        verify=False
    )
    cook = r.cookies
    cook_str = ''
    for x in cook:
        cook_str += (x.name + '=' + x.value + ';')
    headers['Cookie'] = cook_str
    # df = pd.read_csv(csv_url, usecols=['date', 'open', 'high', 'low', '0', 'volume', 'close'])
    url = ''
    dt = time.time() * 1000
    if ktype == 'W':
        url = 'https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&period=1week&type=before&begin=%f&end=%f&_=%f' % (
            code, dt - (1498109220602 - 1371965220602), dt, dt)
    elif ktype == 'M':
        url = 'https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&period=1month&type=before&end=%f&_=%f' % (
            code, dt, dt)
    elif ktype == 'D':
        url = 'https://xueqiu.com/stock/forchartk/stocklist.json?symbol=%s&_=%f' % (code, dt)
    record_ret = s.get(url, headers=headers)
    record_ret_json = json.loads(record_ret.text)
    opens = []
    closes = []
    highs = []
    lows = []
    dates = []
    import datetime
    for item in record_ret_json[u'chartlist']:
        timestamp = item[u'timestamp']
        timestamp = round(float(timestamp) / 1000, 0)
        date = datetime.datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')
        opens.append(item[u'open'])
        closes.append(item[u'close'])
        highs.append(item[u'high'])
        lows.append(item[u'low'])
        dates.append(date)

    df = pd.DataFrame({
        'open': opens,
        'close': closes,
        'high': highs,
        'low': lows,
        'date': dates
    })
    df.index = df['date']
    if len(start) > 0:
        df = df[df['date'] >= start]
    return df

"""
股票市值
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_market_cap(code):
    '''
    marketCapital, totalShares
    '''
    s = requests.session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.6",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "s=8h12kjdra3; bid=9f8e558960ffc59db81ccd585ad314ed_is5nt7yr; __utma=1.883182649.1471534174.1471534174.1472446021.2; __utmc=1; __utmz=1.1471534174.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); xq_a_token=0c491a0cbcaaa3d60047e8fe70136358b85b3114; xq_r_token=a372978b648bc0c63bec1ac4e4278052716d9a5b; Hm_lvt_1db88642e346389874251b5a1eded6e3=1471421838,1471936805,1472028850,1472189875; Hm_lpvt_1db88642e346389874251b5a1eded6e3=1472551749",
        "Host": "xueqiu.com",
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/43.0.2357.130 Safari/537.36"
    }

    r = s.get(
        'https://xueqiu.com/S/SH600036',
        headers=headers,
        verify=False
    )
    cook = r.cookies
    cook_str = ''
    for x in cook:
        cook_str += (x.name + '=' + x.value + ';')
    headers['Cookie'] = cook_str
    dt = time.time() * 1000
    symbol = ''

    if re.compile(u"[a-zA-Z]+").search(code, 0) is not None:
        symbol = code
        url = 'https://xueqiu.com/v4/stock/quote.json?code=%s&_=%f&isUSdelay=1' % (code, dt)
    elif len(code) == 5:
        symbol = code
        url = 'https://xueqiu.com/v4/stock/quote.json?code=%s&_=%f' % (code, dt)
    elif len(code) == 6:
        symbol = _code_to_symbol(code)
        url = 'https://xueqiu.com/v4/stock/quote.json?code=%s&_=%f' % (symbol, dt)

    record_ret = s.get(url, headers=headers)
    # print record_ret.text
    record_ret_json = json.loads(record_ret.text)[unicode(symbol.upper())]
    totalShares = record_ret_json[u'totalShares']
    last_close = record_ret_json[u'close']
    marketCapital = record_ret_json[u'marketCapital']
    return float(totalShares)  # * float(last_close)


"""
获取k线数据
由于本人比较懒, 所以没有用start和end来截断dataframe
这个接口可以访问美股,港股,A股(印度股,越南股,日股等等未测试,应该也能用)
访问美股和港股需要翻墙,用的是wsj和aastock
访问港股请输入五位数代码
访问美股请输入英文代码
访问A股请输入六位数代码
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_k_data(code=None, start='', end='',
               ktype='D', autype='qfq',
               index=False,
               retry_count=3,
               pause=0.001):

    # print('tushare.trading.get_k_data', end)
    is_us = False
    if re.compile(u"[a-zA-Z]+").search(code, 0) is not None:
        is_us = True
    symbol = ct.INDEX_SYMBOL[code] if index else _code_to_symbol(code)
    url = ''
    dataflag = ''
    autype = '' if autype is None else autype
    # if (start is not None) & (start != ''):
    #     end = du.today() if end is None or end == '' else end
    if ktype.upper() in ct.K_LABELS:
        fq = autype if autype is not None else ''
        if code[:1] in ('1', '5') or index:
            fq = ''
        kline = '' if autype is None else 'fq'
        if end is None or end == '':
            if len(code) == 5:
                kline = 'hkfq'
            if is_us:
                kline = 'usfq'
            urls = [ct.KLINE_TT_URL % (ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                   kline, fq, symbol,
                                   ct.TT_K_TYPE[ktype.upper()], start, end,
                                   fq, _random(17))]
        else:
            years = du.tt_dates(start, end)
            urls = []
            for year in years:
                startdate = str(year) + '-01-01'
                enddate = str(year + 1) + '-06-30'
                url = ct.KLINE_TT_URL % (ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                         kline, fq + str(year), symbol,
                                         ct.TT_K_TYPE[ktype.upper()], startdate, enddate,
                                         fq, _random(17))
                urls.append(url)
        dataflag = '%s%s' % (fq, ct.TT_K_TYPE[ktype.upper()])
    elif ktype in ct.K_MIN_LABELS:
        if len(code) == 5:
            urls = ['http://web.ifzq.gtimg.cn/appstock/app/day/query?_var=fdays_data_%s&code=%s&r=0.%s' % (
                symbol, symbol, _random(16))]
            dataflag = 'data'
        else:
            urls = [ct.KLINE_TT_MIN_URL % (ct.P_TYPE['http'], ct.DOMAINS['tt'],
                                           symbol, ktype, ktype,
                                           _random(16))]
            dataflag = 'm%s' % ktype
    else:
        raise TypeError('ktype input error.')
    data = pd.DataFrame()
    for url in urls:
        # print(datetime.datetime.now(), '-'*20)
        _temp = _get_k_data(url, dataflag,
                                       symbol, code,
                                       index, ktype,
                                       retry_count, pause)
        data = data.append(_temp,   ignore_index=True)
        # print(datetime.datetime.now(), '-'*20)
    if ktype not in ct.K_MIN_LABELS:
        if ((start is not None) & (start != '')) & ((end is not None) & (end != '')):
            data = data[(data.date >= start) & (data.date <= end)]
    if start is not None and start != '':
        return data[data.date >= start]
    return data

"""
获取前复权价格
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_k_data_qfq(code=None, ktype='5'):
    df_5 = get_k_data(code, ktype=ktype)
    first_value = None
    need_calculate = False
    for idx2, row2 in df_5.iterrows():
        if first_value is None:
            first_value = row2['close']
            continue
        if first_value / row2['close'] > 1.05:
            need_calculate = True
            break
        first_value = row2['close']
    if need_calculate:
        df_d = get_k_data(code, ktype='D')
        for idx in range(df_d.shape[0] - 2, 0, -1):
            date_ = df_d.iloc[idx]['date']
            close = df_d.iloc[idx]['close']
            result = df_5[df_5['date'] == '%s 15:00' % date_]
            if result.shape[0] == 0:
                break
            bili = result.iloc[0]['close'] / close
            if bili != 1:
                for idx2, row2 in df_5.iterrows():
                    if row2['date'] <= '%s 15:00' % date_:
                        df_5.set_value(idx2, 'close', row2['close'] / bili)
                break
    return df_5

"""
获取ETFk线数据
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_etf_data(code=None, start='', end='',
                 ktype='D', autype='qfq',
                 index=False,
                 retry_count=3,
                 pause=0.001):
    url = 'http://stockjs.finance.qq.com/fundUnitNavAll/data/year_all/%s.js' % code
    lines = None
    try:
        request = Request(url)
        lines = urlopen(request, timeout=10).read()
        if len(lines) < 100:  # no data
            return None
    except Exception as e:
        print(e)
    lines = lines.split('=')[1]
    df = get_k_data(code, start, end, ktype, autype, index, retry_count, pause)
    df.index = df['date']
    for item in json.loads(lines)[u'data']:
        date = str(item[0])
        nav = item[2]
        df.set_value('%s-%s-%s' % (date[:4], date[4:6], date[6:]), 'nav', float(nav))
    df = df.sort_index()
    for i in range(0, df.shape[0]):
        if np.isnan(df.iloc[i]['nav']):
            df.set_value(df.index[i], 'nav', df.iloc[i - 1]['nav'])
    return df


# 为了第二次访问的时候, 速度更快, 所以先建立session
session = requests.session()
def _get_k_data(url, dataflag='',
                symbol='',
                code='',
                index=False,
                ktype='',
                retry_count=1,
                pause=0.001):
    # print (url)
    for _ in range(retry_count):
        # print(_)
        # if _ > 0:
        #     time.sleep(pause)
        try:
            # request = Request(url)
            # lines = urlopen(request, timeout=10).read()
            # lines = urlopen(url).read()
            lines = session.get(url).content.decode('utf-8')
            if len(lines) < 100:  # no data
                return None
        except Exception as e:
            print(e)
        else:
            # lines = lines.decode('utf-8') if ct.PY3 else lines
            lines = lines.split('=')[1]
            reg = re.compile(r',{"(nd|cqr).*?}')
            lines = re.subn(reg, '', lines)
            js = json.loads(lines[0])
            dataflag = dataflag if dataflag in list(js['data'][symbol].keys()) else ct.TT_K_TYPE[ktype.upper()]
            if len(code) == 5 and ktype == '5':
                results = []
                for item in js['data'][symbol][dataflag]:
                    for row in item[u'data']:
                        if len(row) != 0:
                            cols = row.split(' ')
                            col_t = cols[0]
                            col_price = cols[1]
                            if int(col_t) % 5 == 0:
                                results.append({'date': '%s %s' % (item[u'date'], col_t), 'price': col_price})
                return pd.DataFrame(results).sort_values(by='date', ascending=True)
            else:
                if symbol.find('us') == 0:
                    totals = []
                    for i in js['data'][symbol][dataflag]:
                        totals.append(i[:6])
                    df = pd.DataFrame(totals, columns=ct.KLINE_TT_COLS)
                elif len(code) == 5:
                    df = pd.DataFrame(js['data'][symbol][dataflag], columns=ct.KLINE_HKTT_COLS)
                else:
                    df = pd.DataFrame(js['data'][symbol][dataflag], columns=ct.KLINE_TT_COLS)
                df['code'] = symbol if index else code
                if ktype in ct.K_MIN_LABELS:
                    df['date'] = df['date'].map(lambda x: '%s-%s-%s %s:%s' % (x[0:4], x[4:6],
                                                                              x[6:8], x[8:10],
                                                                              x[10:12]))
                for col in df.columns[1:6]:
                    df[col] = df[col].astype(float)
                return df


def get_hists(symbols, start=None, end=None,
              ktype='D', retry_count=3,
              pause=0.001):
    """
    批量获取历史行情数据，具体参数和返回数据类型请参考get_hist_data接口
    """
    df = pd.DataFrame()
    if isinstance(symbols, list) or isinstance(symbols, set) or isinstance(symbols, tuple) or isinstance(symbols,
                                                                                                         pd.Series):
        for symbol in symbols:
            data = get_hist_data(symbol, start=start, end=end,
                                 ktype=ktype, retry_count=retry_count,
                                 pause=pause)
            data['code'] = symbol
            df = df.append(data, ignore_index=True)
        return df
    else:
        return None


def _random(n=13):
    from random import randint
    start = 10 ** (n - 1)
    end = (10 ** n) - 1
    return str(randint(start, end))


"""
获取涨跌停价格
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def calculate_zhangdieting(close, max_zf):
    max_zf = max_zf + 1
    new_price = round(close * max_zf, 2)
    def _get_abs(_price):
        return abs(_price / close - max_zf)

    if _get_abs(new_price + 0.01) < _get_abs(new_price):
        new_price = new_price + 0.01

    if _get_abs(new_price - 0.01) < _get_abs(new_price):
        new_price = new_price - 0.01
    zhangting = new_price

    def _get_abs_dt(_price):
        return abs(_price / close - 2 + max_zf)

    new_price = round(close * (2-max_zf), 2)
    if _get_abs_dt(new_price + 0.01) < _get_abs_dt(new_price):
        new_price = new_price + 0.01
    if _get_abs_dt(new_price - 0.01) < _get_abs_dt(new_price):
        new_price = new_price - 0.01
    dieting = new_price
    return (zhangting, dieting)

"""
获取涨跌停价格
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def calculate_zhangdieting_with_code(code, close):
    max_zf = 0.1
    if code.find('300') == 0 or code.find('301') == 0 or code.find('688') == 0:
        max_zf = 0.2
    return calculate_zhangdieting(close, max_zf)

"""
获取涨跌停价格
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def getZhangDieTing(code):
    # df = get_k_data(code, start='2022-11-01')
    df = get_k_data(code)
    assert df is not None
    close = df.iloc[-2]['close']
    (zhangting, dieting) = calculate_zhangdieting_with_code(code, close)
    return (zhangting, dieting, df.iloc[-1]['close'])

