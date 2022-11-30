__version__ = '0.6.2'
__author__ = 'Jimmy Liu'

"""
for trading data
"""
from tushare.stock.trading import (set_use_cache, get_hist_data, get_tick_data,
                                   get_realtime_quotes,
                                   get_h_data, get_today_ticks,
                                   get_index, get_hists, get_profit_yoy,
                                   get_k_data, get_cfst,get_sina_caiwu_index,
                                   get_sina_dd, get_etf_data,
                                   get_debtpaying, get_profit, get_operation, get_growth,
                                   get_djcw, get_mfratio, get_cbsheet,get_cbsheet_us,get_inst_us,get_cashflow_us, get_aastock_balance_sheet, get_wsj_hk_income_statement, get_wsj_hk_predict_pe, get_aastock_profit_loss, get_aastock_cash_flow,
                                   get_wsj_hk_free_cash_flow,get_aastock_buyback,get_wsj_balance_sheet,set_current_year_season,
                                   get_inst, get_k_data_qfq, get_market_cap, getZhangDieTing)

get_k_data('000651', start='2022-11-01')

"""
for trading data
"""
# from tushare.stock.fundamental import (get_stock_basics, get_report_data,get_report_data_by_code,get_stockstructure_data_by_code,get_cashflow_data_by_code,get_profitstat_data_by_code,
#                                        get_profit_data,
#                                        get_operation_data, get_growth_data,
#                                        get_debtpaying_data, get_cashflow_data, get_profit_predictdc, get_profit_predictths, get_cbsheet_by_code)
# from tushare.trader.trader import TraderAPI

"""
for macro data
"""
# from tushare.stock.macro import (get_gdp_year, get_gdp_quarter,
#                                  get_gdp_for, get_gdp_pull,
#                                  get_gdp_contrib, get_cpi,
#                                  get_ppi, get_deposit_rate,
#                                  get_loan_rate, get_rrr,
#                                  get_money_supply, get_money_supply_bal)

"""
for classifying data
"""
# from tushare.stock.classifying import (get_industry_classified, get_concept_classified,
#                                        get_area_classified, get_gem_classified,
#                                        get_sme_classified, get_st_classified,
#                                        get_hs300s, get_sz50s, get_zz500s,
#                                        get_terminated, get_suspended)

"""
for macro data
"""
# from tushare.stock.newsevent import (get_latest_news, latest_content,
#                                      get_notices, notice_content,
#                                      guba_sina)

"""
for reference
"""
# from tushare.stock.reference import (profit_data, forecast_data,
#                                      xsg_data, fund_holdings,
#                                      new_stocks, sh_margins,
#                                      sh_margin_details,
#                                      sz_margins, sz_margin_details,
#                                      top10_holders)

"""
for shibor
"""
# from tushare.stock.shibor import (shibor_data, shibor_quote_data,
#                                   shibor_ma_data, lpr_data,
#                                   lpr_ma_data)

"""
for LHB
"""
# from tushare.stock.billboard import (top_list, cap_tops, broker_tops,
#                                      inst_tops, inst_detail)


"""
for utils
"""
# from tushare.util.dateu import (trade_cal, is_holiday)


"""
for DataYes Token
"""
# from tushare.util.upass import (set_token, get_token, get_broker,
#                                 set_broker, remove_broker)
#
# from tushare.internet.boxoffice import (realtime_boxoffice, day_boxoffice,
#                                         day_cinema, month_boxoffice)
