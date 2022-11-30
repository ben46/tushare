# -*- coding:utf-8 -*- 
"""
基本面数据接口 
Created on 2015/01/18
@author: Jimmy Liu
@group : waditu
@contact: jimmysoa@sina.cn
"""
import pandas as pd
from tushare.stock import cons as ct
import lxml.html
from lxml import etree
import re
from pandas.compat import StringIO
import time
from tushare.stock.trading import _code_to_symbol
import datetime
import tushare as ts
import json
import os

try:
    from urllib.request import urlopen, Request
except ImportError:
    from urllib2 import urlopen, Request

def get_stock_basics():
    """
        获取沪深上市公司基本情况
    Return
    --------
    DataFrame
               code,代码
               name,名称
               industry,细分行业
               area,地区
               pe,市盈率
               outstanding,流通股本
               totals,总股本(万)
               totalAssets,总资产(万)
               liquidAssets,流动资产
               fixedAssets,固定资产
               reserved,公积金
               reservedPerShare,每股公积金
               eps,每股收益
               bvps,每股净资
               pb,市净率
               timeToMarket,上市日期
    """
    request = Request(ct.ALL_STOCK_BASICS_FILE)
    text = urlopen(request, timeout=60).read()
    text = text.decode('GBK')
    text = text.replace('--', '')
    df = pd.read_csv(StringIO(text), dtype={'code':'object'})
    df = df.set_index('code')
    return df

def get_report_data(year, quarter):
    """
        获取业绩报表数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        eps,每股收益
        eps_yoy,每股收益同比(%)
        bvps,每股净资产
        roe,净资产收益率(%)
        epcf,每股现金流量(元)
        net_profits,净利润(万元)
        profits_yoy,净利润同比(%)
        distrib,分配方案
        report_date,发布日期
    """
    if ct._check_input(year,quarter) is True:
        ct._write_head()
        df =  _get_report_data(year, quarter, 1, pd.DataFrame())
        if df is not None:
#             df = df.drop_duplicates('code')
            df['code'] = df['code'].map(lambda x:str(x).zfill(6))
        return df

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_stockstructure_data_by_code(code, retry_count=3, pause=5):
    for _ in range(retry_count):
        try:
            _url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockStructure/stockid/'+code + '.phtml'
            print(_url)
            __cache_file_path = '%s%s' % (ct.CACHE_DIR, _url.replace('/', ''))
            if os.path.exists(__cache_file_path) and 1:
                print ('read from cache', __cache_file_path)
                return pd.read_csv(__cache_file_path)
            request = Request(_url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('gb2312')
            text = text.replace('--', '')
            html = lxml.html.parse(StringIO(text))
            res_1 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[1]/td[position()>1]")
            res_5 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[5]/td[position()>1]")
            arr_1 = [date.text for date in res_1]
            arr_5 = [float(date.text[:-2]) for date in res_5]
            df = pd.DataFrame()
            df['date'] = arr_1
            df['shares'] = arr_5
            print ('save to cache', __cache_file_path)
            df.to_csv(__cache_file_path)
            time.sleep(20)
            return df
        except Exception as e:
            print(e)
            time.sleep(pause)
            _url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vCI_StockStructure/stockid/' + code + '.phtml'
            if os.path.exists(__cache_file_path):
                print ('read from cache', __cache_file_path)
                return pd.read_csv(__cache_file_path)
            request = Request(_url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('gbk')
            text = text.replace('--', '')
            html = lxml.html.parse(StringIO(text))
            res_1 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[1]/td[position()>1]")
            res_5 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[5]/td[position()>1]")
            arr_1 = [date.text for date in res_1]
            arr_5 = [float(date.text[:-2]) for date in res_5]
            df = pd.DataFrame()
            df['date'] = arr_1
            df['shares'] = arr_5
            print ('save to cache', __cache_file_path)
            df.to_csv(__cache_file_path)
            time.sleep(20)
            return df
    raise IOError(ct.NETWORK_URL_ERROR_MSG)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_profit_predictdc(code, retry_count=3, pause=5):
    '''
    获取机构预测利润, 东方财富
    '''
    for _ in range(retry_count):
        try:
            url = 'http://emweb.securities.eastmoney.com/PC_HSF10/ProfitForecast/ProfitForecastAjax?code=%s' % _code_to_symbol(code)
            print (url)
            request = Request(url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('utf8')
            text = text.replace('--', '')
            if 0:
                html = lxml.html.parse(StringIO(text))
                res = html.xpath('/html/body/div[1]/div[14]/div[3]/table')
                resstr = etree.tostring(res[0]).decode('utf-8')
                print (resstr)
                df = pd.read_html(resstr)[0]
                df = df.transpose()
                df.columns = df.iloc[0]
                df = df.drop(0, axis=0)
                profit_strs = list(df[u'归属于母公司股东的净利润(元)'])
                profits = []
                for profit_str in profit_strs:
                    if isinstance(profit_str, unicode):
                        if profit_str.find('亿') != -1:
                            profits.append(float(profit_str.split('亿')[0]) * 10000)
                        elif profit_str.find('万') != -1:
                            profits.append(float(profit_str.split('万')[0]))
                        else:
                            profits.append(0)
                    else:
                        profits.append(0)
                df['profit'] = profits
                df.index = range(df.shape[0])
                return df
            else:
                results = json.loads(text)
                profits = []
                years = []
                for data in results['Result']['yctj']['data']:
                    year = data['rq'].split('年')[0]
                    years.append(int(year))
                    profit_str = data['jlr']
                    if profit_str.find('亿') != -1:
                        profits.append(float(profit_str.split('亿')[0]) * 10000)
                    elif profit_str.find('万') != -1:
                        profits.append(float(profit_str.split('万')[0]))
                    else:
                        profits.append(0)
                return pd.DataFrame({"profit": profits,
                                     'year': years})
        except Exception as e:
            print(e)
            time.sleep(pause)
    raise IOError(ct.NETWORK_URL_ERROR_MSG)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_profit_predictths(code, retry_count=3, pause=5):
    '''
    获取机构预测利润,童虎顺
    '''
    for _ in range(retry_count):
        try:
            url = 'http://stockpage.10jqka.com.cn/%s/worth/#forecast' % code
            print (url)
            request = Request(url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('utf8')
            text = text.replace('--', '')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath('//*[@class="m_table m_hl"]')
            resstr = etree.tostring(res[1]).decode('utf-8')
            df = pd.read_html(resstr)[0]
            df[u'均值'] = df[u'均值']  * 10000
            return df
        except Exception as e:
            print(e)
            time.sleep(pause)
    return None
"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_cashflow_data_by_code(code):
    try:
        _url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vFD_CashFlow/stockid/'+code + '/ctrl/all/displaytype/4.phtml'
        print (_url)
        request = Request(_url)
        text = urlopen(request, timeout=60).read()
        text = text.decode('gb2312')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res_1 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[1]/td[position()>1]")
        res_5 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[28]/td[position()>1]")
        arr_1 = [date.text for date in res_1]
        arr_5 = [float(date.text.replace(',','')) for date in res_5]
        df = pd.DataFrame()
        df['date'] = arr_1
        df['cashflow'] = arr_5
        return df
    except Exception as e:
        print(e)

"""
http://money.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/600332/ctrl/part/displaytype/4.phtml
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_profitstat_data_by_code(code, retry_count=3, pause=5):
    for _ in range(retry_count):
        try:
            _url = 'http://vip.stock.finance.sina.com.cn/corp/go.php/vFD_ProfitStatement/stockid/'+code + '/ctrl/all/displaytype/4.phtml'
            print (_url)
            request = Request(_url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('gb2312')
            text = text.replace('--', '')
            html = lxml.html.parse(StringIO(text))
            res_1 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[1]/td[position()>1]")
            res_5 = html.xpath("//div[@id=\"con02-1\"]/table/tbody/tr[3]/td[position()>1]")
            arr_1 = [date.text for date in res_1]
            arr_5 = [float(date.text.replace(',','')) for date in res_5]
            df = pd.DataFrame()
            df['date'] = arr_1
            df['income'] = arr_5
            return df
        except Exception as e:
            print(e)
            time.sleep(pause)
    raise IOError(ct.NETWORK_URL_ERROR_MSG)

"""
Created on 2022/11/30
@author: Charlie Zhou
@contact: ben02060846@qq.com
"""
def get_report_data_by_code(code, retry_count=3, pause=5):
    for _ in range(retry_count):
        try:
            _url = 'http://vip.stock.finance.sina.com.cn/q/go.php/vFinanceAnalyze/kind/mainindex/index.phtml?symbol='+code
            print (_url)
            request = Request(_url)
            text = urlopen(request, timeout=60).read()
            text = text.decode('GBK')
            text = text.replace('--', '')
            html = lxml.html.parse(StringIO(text))
            res = html.xpath("//table[@class=\"list_table\"]/tr")
            if ct.PY3:
                sarr = [etree.tostring(node).decode('utf-8') for node in res]
            else:
                sarr = [etree.tostring(node) for node in res]
            sarr = ''.join(sarr)
            sarr = '<table>%s</table>'%sarr
            df = pd.read_html(sarr)[0]
            df = df.drop(11, axis=1)
            df.columns = ct.REPORT_COLS
            df = df.sort_values(by='name', ascending=False)  # 根据时间排序
            return df
        except Exception as e:
            time.sleep(pause)
            print (e)
    raise IOError(ct.NETWORK_URL_ERROR_MSG)

from importlib import reload
import sys
# reload(sys)
# sys.setdefaultencoding("UTF8")


def get_cbsheet_by_code(code, start_year=2006):
    cbdf_list = []
    for year in range(start_year, datetime.date.today().year + 1):
        cbdf = ts.get_cbsheet(code, year)
        if cbdf is not None:
            cbdf_list.append(cbdf)
    cbdf = pd.concat(cbdf_list)  # 因为时间段而拆分的价格数据, 重新拼接
    cbdf = cbdf.sort_index(ascending=False)  # 根据时间排序
    cbdf = cbdf[pd.notnull(cbdf.index)]

    if u'归属于母公司的股东权益合计' in cbdf.columns:
        cbdf['net_assets'] = cbdf[u'归属于母公司的股东权益合计']
    elif u'归属于母公司股东权益合计' in cbdf.columns:
        cbdf['net_assets'] = cbdf[u'归属于母公司股东权益合计']
    elif u'归属于母公司股东的权益' in cbdf.columns:
        cbdf['net_assets'] = cbdf[u'归属于母公司股东的权益']
    return cbdf


def _get_report_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        _url = ct.REPORT_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'], ct.PAGES['fd'],
                         year, quarter, pageNo, ct.PAGE_NUM[1])
        print (_url)
        request = Request(ct.REPORT_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'], ct.PAGES['fd'],
                         year, quarter, pageNo, ct.PAGE_NUM[1]))
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df = df.drop(11, axis=1)
        df.columns = ct.REPORT_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage)>0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_report_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except Exception as e:
        print(e)


def get_profit_data(year, quarter):
    """
        获取盈利能力数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        roe,净资产收益率(%)
        net_profit_ratio,净利率(%)
        gross_profit_rate,毛利率(%)
        net_profits,净利润(万元)
        eps,每股收益
        business_income,营业收入(百万元)
        bips,每股主营业务收入(元)
    """
    if ct._check_input(year, quarter) is True:
        ct._write_head()
        data =  _get_profit_data(year, quarter, 1, pd.DataFrame())
        if data is not None:
#             data = data.drop_duplicates('code')
            data['code'] = data['code'].map(lambda x:str(x).zfill(6))
        return data


def _get_profit_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        request = Request(ct.PROFIT_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                              ct.PAGES['fd'], year,
                                              quarter, pageNo, ct.PAGE_NUM[1]))
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df.columns=ct.PROFIT_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage)>0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_profit_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except:
        pass


def get_operation_data(year, quarter):
    """
        获取营运能力数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        arturnover,应收账款周转率(次)
        arturndays,应收账款周转天数(天)
        inventory_turnover,存货周转率(次)
        inventory_days,存货周转天数(天)
        currentasset_turnover,流动资产周转率(次)
        currentasset_days,流动资产周转天数(天)
    """
    if ct._check_input(year, quarter) is True:
        ct._write_head()
        data =  _get_operation_data(year, quarter, 1, pd.DataFrame())
        if data is not None:
#             data = data.drop_duplicates('code')
            data['code'] = data['code'].map(lambda x:str(x).zfill(6))
        return data


def _get_operation_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        request = Request(ct.OPERATION_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                                 ct.PAGES['fd'], year,
                                                 quarter, pageNo, ct.PAGE_NUM[1]))
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df.columns=ct.OPERATION_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage)>0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_operation_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except Exception as e:
        print(e)


def get_growth_data(year, quarter):
    """
        获取成长能力数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        mbrg,主营业务收入增长率(%)
        nprg,净利润增长率(%)
        nav,净资产增长率
        targ,总资产增长率
        epsg,每股收益增长率
        seg,股东权益增长率
    """
    if ct._check_input(year, quarter) is True:
        ct._write_head()
        data =  _get_growth_data(year, quarter, 1, pd.DataFrame())
        if data is not None:
#             data = data.drop_duplicates('code')
            data['code'] = data['code'].map(lambda x:str(x).zfill(6))
        return data


def _get_growth_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        _url = ct.GROWTH_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                              ct.PAGES['fd'], year,
                                              quarter, pageNo, ct.PAGE_NUM[1])
        print (_url)
        request = Request(ct.GROWTH_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                              ct.PAGES['fd'], year,
                                              quarter, pageNo, ct.PAGE_NUM[1]))
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if len(res) == 0:
            return None
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df.columns=ct.GROWTH_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        # print dataArr
        # return dataArr
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage) > 0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_growth_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except Exception as e:
        print(e)
        return _get_growth_data(year, quarter, pageNo, dataArr)

def get_debtpaying_data(year, quarter):
    """
        获取偿债能力数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        currentratio,流动比率
        quickratio,速动比率
        cashratio,现金比率
        icratio,利息支付倍数
        sheqratio,股东权益比率
        adratio,股东权益增长率
    """
    if ct._check_input(year, quarter) is True:
        ct._write_head()
        df =  _get_debtpaying_data(year, quarter, 1, pd.DataFrame())
        if df is not None:
#             df = df.drop_duplicates('code')
            df['code'] = df['code'].map(lambda x:str(x).zfill(6))
        return df


def _get_debtpaying_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        request = Request(ct.DEBTPAYING_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                                  ct.PAGES['fd'], year,
                                                  quarter, pageNo, ct.PAGE_NUM[1]))
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df.columns = ct.DEBTPAYING_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage)>0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_debtpaying_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except Exception as e:
        print(e)
 
 
def get_cashflow_data(year, quarter):
    """
        获取现金流量数据
    Parameters
    --------
    year:int 年度 e.g:2014
    quarter:int 季度 :1、2、3、4，只能输入这4个季度
       说明：由于是从网站获取的数据，需要一页页抓取，速度取决于您当前网络速度
       
    Return
    --------
    DataFrame
        code,代码
        name,名称
        cf_sales,经营现金净流量对销售收入比率
        rateofreturn,资产的经营现金流量回报率
        cf_nm,经营现金净流量与净利润的比率
        cf_liabilities,经营现金净流量对负债比率
        cashflowratio,现金流量比率
    """
    if ct._check_input(year, quarter) is True:
        ct._write_head()
        df =  _get_cashflow_data(year, quarter, 1, pd.DataFrame())
        if df is not None:
#             df = df.drop_duplicates('code')
            df['code'] = df['code'].map(lambda x:str(x).zfill(6))
        return df


def _get_cashflow_data(year, quarter, pageNo, dataArr):
    ct._write_console()
    try:
        url = ct.CASHFLOW_URL%(ct.P_TYPE['http'], ct.DOMAINS['vsf'],
                                                ct.PAGES['fd'], year,
                                                quarter, pageNo, ct.PAGE_NUM[1])
        print (url)
        request = Request(url)
        text = urlopen(request, timeout=60).read()
        text = text.decode('GBK')
        text = text.replace('--', '')
        html = lxml.html.parse(StringIO(text))
        res = html.xpath("//table[@class=\"list_table\"]/tr")
        if ct.PY3:
            sarr = [etree.tostring(node).decode('utf-8') for node in res]
        else:
            sarr = [etree.tostring(node) for node in res]
        sarr = ''.join(sarr)
        sarr = '<table>%s</table>'%sarr
        df = pd.read_html(sarr)[0]
        df.columns = ct.CASHFLOW_COLS
        dataArr = dataArr.append(df, ignore_index=True)
        nextPage = html.xpath('//div[@class=\"pages\"]/a[last()]/@onclick')
        if len(nextPage)>0:
            pageNo = re.findall(r'\d+', nextPage[0])[0]
            return _get_cashflow_data(year, quarter, pageNo, dataArr)
        else:
            return dataArr
    except Exception as e:
        print(e)
       
       
def _data_path():
    import os
    import inspect
    caller_file = inspect.stack()[1][1]  
    pardir = os.path.abspath(os.path.join(os.path.dirname(caller_file), os.path.pardir))
    return os.path.abspath(os.path.join(pardir, os.path.pardir))

