from os import error
from typing import Dict
from django.shortcuts import render
from django.views.generic import View
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from django.utils import timezone as datetime
from django.conf import settings

from itertools import islice
import pandas as pd
from asgiref.sync import AsyncToSync, SyncToAsync
import plotly.graph_objects as go
from plotly.offline import plot
from futu import *
import pytz, csv, math
from .models import *
from .serializers import warrant_market_closed_Serializer #, warrant_transaction_Serializer

# from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class warrant_market_closed_ViewSet(viewsets.ModelViewSet):
    queryset = warrant_market_closed.objects.all()
    serializer_class = warrant_market_closed_Serializer
    permission_classes = (IsAuthenticated,)

class futu_Api():
    def __init__(self):
        self.quote_ctx = OpenQuoteContext(host="0.0.0.0", port=11111)
        self.REST_TIME = 10

    def close(self):
        return self.quote_ctx.close()

    def query_subscription(self):
        status, out_put = self.quote_ctx.query_subscription()
        return out_put

    def subscribe(self, code, subscribe_list=['QUOTE', 'TICKER', 'K_DAY', 'ORDER_BOOK', 'RT_DATA', 'BROKER']):
        subtype_list = []
        if type(code) != list:
            code = [code]
        if 'QUOTE' in subscribe_list:
            subtype_list.append(SubType.QUOTE)
        if 'TICKER' in subscribe_list:
            subtype_list.append(SubType.TICKER)
        if 'K_DAY' in subscribe_list:
            subtype_list.append(SubType.K_DAY)
        if 'ORDER_BOOK' in subscribe_list:
            subtype_list.append(SubType.ORDER_BOOK)
        if 'RT_DATA' in subscribe_list:
            subtype_list.append(SubType.RT_DATA)
        if 'BROKER' in subscribe_list:
            subtype_list.append(SubType.BROKER)
        return self.quote_ctx.subscribe(code, subtype_list)

    def unsubscribe(self, code):
        if type(code) != list:
            code = [code]
        subtype_list = [SubType.QUOTE, SubType.TICKER, SubType.K_DAY, SubType.ORDER_BOOK, SubType.RT_DATA, SubType.BROKER]
        return self.quote_ctx.unsubscribe(code, subtype_list)

    def get_warrant(self, stock_owner, req_num: int=200, type_list=['CALL'], delta=None) -> pd.DataFrame:  #Input:Str Output:Df / 60 Times in 30s
        req = WarrantRequest()
        req.num = req_num
        req.begin = 0
        req.type_list = type_list
        # BULL BEAR has no delta
        if 'BEAR' not in type_list and 'BULL' not in type_list:
            if not delta:
                delta = (-1,1)
            req.delta_min, req.delta_max = delta
        req.status = 'NORMAL'

        out_puts = []
        while True:
            out_put = self.quote_ctx.get_warrant(stock_owner, req)   #First
            if isinstance(out_put[1][0], pd.core.frame.DataFrame):
                out_puts.append(out_put[1][0])
                if len(out_put[1][0]) < 200:
                    return pd.concat(out_puts)
                else:
                    req.begin += 200
            else:
                print('get_warrant: ', out_put)
                time.sleep(self.REST_TIME)

    def get_capital_flow(self, code) -> pd.DataFrame:  #Input:Str Output:Df / 30 Times in 30s
        while True:
            status, out_put = self.quote_ctx.get_capital_flow(code)
            if isinstance(out_put, pd.core.frame.DataFrame):
                return out_put
            else:
                print(out_put)
                time.sleep(self.REST_TIME)

    def get_capital_distribution(self, code) -> pd.DataFrame:  #Input:Str Output:Df / 30 Times in 30s
        while True:
            status, out_put = self.quote_ctx.get_capital_distribution(code)
            if isinstance(out_put, pd.core.frame.DataFrame):
                return out_put
            else:
                print(out_put)
                time.sleep(self.REST_TIME)

    def get_market_snapshot(self, code) -> pd.DataFrame:  #Input:List Output:Df / 60 Times in 30s
        if type(code) != list:
            code = [str(code)]
        else:
            if code[0][:3] != 'HK.':
                code = ['HK.' + str(x) for x in code]

        out_put_all = pd.DataFrame()
        while True:
            for i in range(0,math.ceil(len(code)/400)):
                status, out_put = self.quote_ctx.get_market_snapshot(code[i*400:(i+1)*400])
                if isinstance(out_put, pd.core.frame.DataFrame):
                    out_put_all = pd.concat([out_put_all, out_put], ignore_index=True, sort=False)
                else:
                    i -= 1
                    time.sleep(self.REST_TIME / 3) # Try shorter Time period
            if isinstance(out_put, pd.core.frame.DataFrame):
                break
            else:
                print('<get_market_snapshot>:', code, 'Times:', i, 'feedback: ', out_put)
                time.sleep(self.REST_TIME)
        return out_put_all

    def get_order_book(self, code) -> Dict:  #Input:Str Output:Dict / Subscribe
        self.quote_ctx.subscribe(code, 'ORDER_BOOK')
        while True:
            status, out_put = self.quote_ctx.get_order_book(code)
            if isinstance(out_put, dict):
                self.quote_ctx.unsubscribe(code, 'ORDER_BOOK')
                return out_put
            else:
                self.quote_ctx.subscribe(code, 'ORDER_BOOK')
                self.quote_ctx.unsubscribe_all()
                print('<get_order_book>: ', code, 'feedback: ',  out_put)
                time.sleep(self.REST_TIME)

    def get_rt_data(self, code) -> pd.DataFrame:  #Input:Str Output:Df / Subscribe
        self.quote_ctx.subscribe(code, 'RT_DATA')
        while True:
            status, out_put = self.quote_ctx.get_rt_data(code)
            if isinstance(out_put, pd.core.frame.DataFrame):
                self.quote_ctx.unsubscribe(code, 'RT_DATA')
                return out_put
            else:
                self.quote_ctx.subscribe(code, 'RT_DATA')
                self.quote_ctx.unsubscribe_all()
                print('<get_rt_data>: ', code, 'feedback: ', out_put)
                time.sleep(self.REST_TIME)

    def get_rt_ticker(self, code, ignore_error=False) -> pd.DataFrame:   #Input:Str Output:Df / Subscribe
        self.quote_ctx.subscribe(code, 'TICKER')
        while True:
            status, out_put = self.quote_ctx.get_rt_ticker(code)
            if isinstance(out_put, pd.core.frame.DataFrame):
                self.quote_ctx.unsubscribe(code, 'TICKER')
                return out_put
            else:
                self.quote_ctx.subscribe(code, 'TICKER')
                self.quote_ctx.unsubscribe_all()
                if not ignore_error:
                    print('<get_rt_ticker>: ', code, 'feedback: ', out_put)
                time.sleep(self.REST_TIME)

    def get_cur_kline(self, code, num: int=5) -> pd.DataFrame:  #Input:Str Output:Df / Subscribe
        self.quote_ctx.subscribe(code, 'K_1M')
        while True:
            status, out_put = self.quote_ctx.get_cur_kline(code, num, 'K_1M')
            if isinstance(out_put, pd.core.frame.DataFrame):
                # self.quote_ctx.unsubscribe(code,'K_1M')
                return out_put
            else:
                self.quote_ctx.subscribe(code, 'K_1M')
                self.quote_ctx.unsubscribe_all()
                print('<get_cur_kline>: ', code, 'feedback: ', out_put)
                time.sleep(self.REST_TIME)

    def get_stock_quote(self, code) -> pd.DataFrame:  #Input:List Output:Df / Subscribe
        if type(code) != list:
            code = [code]

        ret_sub, err_message = self.quote_ctx.subscribe(code, [SubType.QUOTE], subscribe_push=False)
        if ret_sub == RET_OK:
            while True:
                status, out_put = self.quote_ctx.get_stock_quote(code)
                if isinstance(out_put, pd.core.frame.DataFrame):
                    return out_put
                else:
                    print('<get_stock_quote>: ', code, 'feedback: ', out_put)
                    self.quote_ctx.unsubscribe_all()
                    time.sleep(self.REST_TIME)
        print(err_message)
        return None

    ##Todo 
    def maximum_request_handler(self, code, request): ##Not Working
        if request[0] == -1:
            self.subscribe(code)
        return request[1]

@SyncToAsync
def futu_to_db(code=None, obj=None, db_model: list=None, stock_dict=None, stocks_dict=None, current_time=None):
    batch_size = 400
    if 'warrant_market_closed' in db_model:
        code                    = obj['code'][3:]
        update_timestamp        = datetime.strptime(obj['update_time'], "%Y-%m-%d %H:%M:%S")

        warrant_market_closed.objects.get_or_create(code=code, update_timestamp=update_timestamp,
            defaults={
            'code'                         : code,
            'name'                         : '',
            'stock_owner'                  : hk_stock.objects.get_or_create(code=obj['stock_owner'][3:])[0],
            'last_price'                   : obj['last_price'],
            'open_price'                   : obj['open_price'],
            'high_price'                   : obj['high_price'],
            'low_price'                    : obj['low_price'],
            'prev_close_price'             : obj['prev_close_price'],
            'price_spread'                 : obj['price_spread'],
            'wrt_strike_price'             : obj['wrt_strike_price'],
            'wrt_break_even_point'         : obj['wrt_break_even_point'],
            'wrt_conversion_price'         : obj['wrt_conversion_price'],

            'volume'                       : obj['volume'],
            'wrt_street_vol'               : obj['wrt_street_vol'],
            'wrt_issue_vol'                : obj['wrt_issue_vol'],
            'wrt_street_ratio'             : obj['wrt_street_ratio'],

            'listing_date'                 : datetime.strptime(obj['listing_date'], "%Y-%m-%d"),
            'wrt_maturity_date'            : datetime.strptime(obj['wrt_maturity_date'], "%Y-%m-%d"),
            'wrt_end_trade'                : datetime.strptime(obj['wrt_end_trade'], "%Y-%m-%d"),

            'wrt_status'                   : obj['sec_status'],
            'wrt_conversion_ratio'         : obj['wrt_conversion_ratio'],
            'wrt_type'                     : obj['wrt_type'],
            'wrt_issuer_code'              : obj['wrt_issuer_code'],

            'wrt_delta'                    : obj['wrt_delta'],
            'wrt_implied_volatility'       : obj['wrt_implied_volatility'],
            'wrt_premium'                  : obj['wrt_premium'],
            'wrt_leverage'                 : obj['wrt_leverage'],
            'wrt_ipop'                     : obj['wrt_ipop'],
            'wrt_score'                    : obj['wrt_score'],
            })

    if 'warrant_transaction' in db_model:
        input_timestamp= datetime.now().strftime("%Y-%m-%d") #todo only when before 00:00
        if not obj:
            object = 'empty'
        
        warrant_market_closed.objects.filter(
                code                     = code, 
                update_timestamp         = input_timestamp).update(
                                                            wrt_transaction = obj
                                                            )

    if 'hk_stock_timescale' in db_model:
        code                             = hk_stock.objects.get_or_create(code=obj['code'][3:])[0]
        update_timestamp                 = pytz.timezone('Asia/Hong_Kong').localize(
                                                                            datetime.strptime(obj['time_key'], 
                                                                            "%Y-%m-%d %H:%M:%S")
                                                                        )
        try: # Error When get_history_stock_data
            price_spread             = stock_dict['price_spread']
        except:
            price_spread             = None

        try:
            hk_stock_timescale.objects.update_or_create(code=code, time=update_timestamp,
            defaults={
                # Price Related
                'last_price'                   : obj['close'],
                'open_price'                   : obj['open'],
                'high_price'                   : obj['high'],
                'low_price'                    : obj['low'],
                'price_spread'                 : price_spread,
                # Volume Related
                'volume'                       : obj['volume'],
                'turnover'                     : obj['turnover'],
                'turnover_rate'                : obj['turnover_rate'],
            })
        except:
            print('hk_stock_timescale Duplicated Error', code)

    if 'hk_stock_timescale_bulk' in db_model: # TODO could upgrade to bulk_update_or_create
        if isinstance(obj, list):
            objs=obj
            print(objs[0])
            qs_list = (hk_stock_timescale(
                                    code=hk_stock.objects.get_or_create(code=obj['code'][3:])[0],
                                    time=pytz.timezone('Asia/Hong_Kong').localize(
                                                                        datetime.strptime(obj['time_key'], 
                                                                        "%Y-%m-%d %H:%M:%S")
                                                                    ),
                                    # Price Related
                                    last_price                   = obj['close'],
                                    open_price                   = obj['open'],
                                    high_price                   = obj['high'],
                                    low_price                    = obj['low'],
                                    price_spread                 = obj['price_spread'],
                                    # Volume Related
                                    volume                       = obj['volume'],
                                    turnover                     = obj['turnover'],
                                    turnover_rate                = obj['turnover_rate'],
                                    ) for obj in objs)
            print(qs_list)
            # while True:
                # batch = list(islice(qs_list, batch_size))
                # if not batch:
                    # break
            #hk_stock_timescale.objects.bulk_create(qs_list, batch_size)

    if 'hk_warrant_timescale' in db_model:
        code                         = hk_warrant.objects.get_or_create(code=obj['code'][3:])[0]
        update_timestamp             = pytz.timezone('Asia/Hong_Kong').localize(
                                                                    datetime.strptime(obj['update_time'], 
                                                                    "%Y-%m-%d %H:%M:%S")
                                                                )

        try:
            hk_warrant_timescale.objects.update_or_create(code=code, time=update_timestamp,
                defaults={
                    # Stock Related
                    'code'                         : code,
                    'ask_price'                    : obj['ask_price'],
                    'bid_price'                    : obj['bid_price'],
                    'ask_vol'                      : obj['ask_vol'],
                    'bid_vol'                      : obj['bid_vol'],
                    'price_spread'                 : obj['price_spread'],
                    'wrt_sensitivity'              : obj['wrt_sensitivity'],

                    # Warrant Related
                    'stock_owner'                  : hk_stock.objects.get_or_create(code=obj['stock_owner'][3:])[0],
                    'stock_ask_price'              : stock_dict['ask_price'],
                    'stock_bid_price'              : stock_dict['bid_price'],
                    'stock_ask_vol'                : stock_dict['ask_vol'],
                    'stock_bid_vol'                : stock_dict['bid_vol'],
                    'stock_price_spread'           : stock_dict['price_spread'],
                })
        except:
            print('hk_warrant_timescale Duplicated Error', code)

    if 'hk_warrant_timescale_bulk' in db_model: # TODO could upgrade to bulk_update_or_create
        if (9 < current_time.hour < 16) or (current_time.hour == 9 and current_time.minute > 30) or (current_time.hour == 16 and current_time.minute < 3):
            qs_list=[]
            for stock_dict in stocks_dict:
                objs = stock_dict['obj'].to_dict('records')
                for obj in objs:
                    qs_list.append (hk_warrant_timescale(
                                            time=current_time,
                                            update_time=pytz.timezone('Asia/Hong_Kong').localize(
                                                                                datetime.strptime(obj['update_time'], 
                                                                                "%Y-%m-%d %H:%M:%S")
                                                                            ),
                                            # Warrant Related
                                            code                           = hk_warrant.objects.get_or_create(code=obj['code'][3:])[0],
                                            ask_price                      = obj['ask_price'],
                                            bid_price                      = obj['bid_price'],
                                            ask_vol                        = obj['ask_vol'],
                                            bid_vol                        = obj['bid_vol'],
                                            price_spread                   = obj['price_spread'],
                                            wrt_sensitivity                = obj['wrt_sensitivity'],

                                            # Stock Related
                                            stock_owner                    = hk_stock.objects.get_or_create(code=obj['stock_owner'][3:])[0],
                                            stock_ask_price                = stock_dict['ask_price'],
                                            stock_bid_price                = stock_dict['bid_price'],
                                            stock_ask_vol                  = stock_dict['ask_vol'],
                                            stock_bid_vol                  = stock_dict['bid_vol'],
                                            stock_price_spread             = stock_dict['price_spread'],
                                    ))

            if not hk_warrant_timescale.objects.bulk_create(qs_list, batch_size, ignore_conflicts=True):
                print('HK warrant Timescale Data Inject Failed')

def get_codes_from_warrant_list():
    with open('account/WARRANT_LIST.csv', newline='') as csvfile:
        reader = csv.reader(csvfile)
        output_list = []
        output_dict = {}

        for row in reader:
            while("" in row) : 
                row.remove("") 

            for i in row[1:]:
                if len(i) < 2:
                    output_list.append('0000' + i)
                elif len(i) < 3:
                    output_list.append('000' + i)
                elif len(i) < 4:
                    output_list.append('00' + i)
                elif len(i) < 5:
                    output_list.append('0' + i)
            output_dict.update({row[0]:output_list[1:]})
    codes = output_dict['\ufeff110000']
    return codes

#############
class calculate_warrant():
    def test():
        with pd.option_context('display.max_rows', None, 'display.max_columns', None):  # more options can be specified also
            quote_ctx.subscribe(code_list, subtype_list ,True , False )

            df = quote_ctx.get_market_snapshot(code_list)
            df = df[1]
            #print(df)

            ask_price = df['ask_price'].values
            bid_price = df['bid_price'].values
            wrt_delta = df['wrt_delta'].values
            wrt_coversion_ratio = df['wrt_conversion_ratio'].values

            spread = ask_price - bid_price
            w_sen = wrt_delta * stock_spread
            flat_position = spread / (wrt_delta * stock_spread / wrt_coversion_ratio) + 1

            print(code)
            print('spread' + str(spread))
            print('w_sen:' + str(w_sen))
            print('falt_postion:' + str(flat_position))

@SyncToAsync
def cal_volume_extreme(code, num_data):
    get_object = hk_stock.objects.get(code=code)
    df = pd.DataFrame(hk_stock_timescale.objects.filter(code=get_object).order_by('-time')[:num_data].values())
    df['diff_volume'] = abs(df['volume'].diff())
    # price_change = round(df.iloc[1]['last_price']- df.iloc[2]['last_price'], 2)
    try:
        if len(df) > 2:
            diff_voluem_muliplier = round(df.iloc[1]['diff_volume'] / df.iloc[2:]['diff_volume'].mean())
            # diff_voluem_muliplier = round(df.iloc[1]['diff_volume'] / df.iloc[2]['diff_volume'])
            return diff_voluem_muliplier
        else:
            return None
    except:
        return None

def plot_table(fig):
    print(type(fig))
    fig = fig.iloc[0:2 ,0:10]
    print(fig)
    fig = go.Figure(data=[go.Table(
                    header=dict(values=list(fig.columns),
                                fill_color='paleturquoise',
                                align='left'),
                    cells=dict(values=[fig.code, fig.last_price, fig.open_price, fig.high_price, fig.low_price],
                            fill_color='lavender',
                            align='left'))
                ])
    plt_div = plot(fig, output_type='div', include_plotlyjs=False)
    return plt_div

### dash ###
def dash(request, **kwargs):
    return HttpResponse(dispatcher(request))

@csrf_exempt
def dash_ajax(request):
    return HttpResponse(dispatcher(request), content_type='application/json')

def traded_positions(rt_ticker):
    x = rt_ticker
    df = rt_ticker.sort_values(['time', 'volume'], ascending=[True, True])

    df_list = list( dict.fromkeys(df['volume'].values) )

    profit_times_list = []
    profit_positions_list = []
    loss_times_list = []
    loss_positions_list = []

    if df.empty is True:
        profit_times_list.append(0)
        profit_positions_list.append(0)
        loss_times_list.append(0)
        loss_positions_list.append(0) 

    summary_df = pd.DataFrame()
    for df_volume in df_list:
        df1 = df[df['volume'].values == df_volume]
        df1 = df1.reset_index()
        df1 = df1.drop(columns = ['index'], axis=1)

        profit_times = 0
        profit_positions = 0
        loss_times = 0
        loss_positions = 0
        for i in range(0 , df1.shape[0]):
            try:
                if df1.iloc[i].ticker_direction == 'BUY':
                    if df1.iloc[i + 1].ticker_direction == 'SELL':
                        df_pair = pd.concat([df1.iloc[i], df1.iloc[i + 1]], axis=1)
                        summary_df = summary_df.append(df_pair.T, ignore_index = True)

                        if df1.iloc[i + 1].values[3] - df1.iloc[i].values[3] > 0:
                            profit_times = profit_times + 1
                            profit_positions = int((df1.iloc[i + 1].values[3] - df1.iloc[i].values[3]) / 0.001)
                        if df1.iloc[i + 1].values[3] - df1.iloc[i].values[3] < 0:
                            loss_times = loss_times + 1
                            loss_positions = int((-df1.iloc[i + 1].values[3] + df1.iloc[i].values[3]) / 0.001)
                        i = i + 1
                else:
                    pass
            except IndexError:
                pass
        profit_times_list.append(profit_times)
        profit_positions_list.append(profit_positions)
        loss_times_list.append(loss_times)
        loss_positions_list.append(loss_positions)

    ###########remained_amount#########
    df1 = pd.concat([summary_df, pd.DataFrame(columns = [ 'transacted amount', 'neutral transacted amount','neutral volume'])], sort=False)
    if 'price' in df1:
        df1['transacted amount'] = df1['price'] * df1['volume']

        df1.loc[df1.ticker_direction == 'BUY', 'neutral transacted amount'] = df1['transacted amount']
        df1.loc[df1.ticker_direction == 'SELL', 'neutral transacted amount'] = -df1['transacted amount']
        df1.loc[df1.ticker_direction == 'NEUTRAL', 'neutral transacted amount'] = -df1['transacted amount']

        df1.loc[df1.ticker_direction == 'BUY', 'neutral volume'] = df1['volume']
        df1.loc[df1.ticker_direction == 'SELL', 'neutral volume'] = -df1['volume']
        df1.loc[df1.ticker_direction == 'NEUTRAL', 'neutral volume'] = -df1['volume']

        transacted_amount = df1['transacted amount'].sum()
        neutral_transacted_amount = df1['neutral transacted amount'].sum()
        neutral_volume = df1['neutral volume'].sum()

        if neutral_volume == 0:
            remained_amount = neutral_transacted_amount
        else:
            overnight_position = df1['price'][df1.shape[0]-1] * neutral_volume
            remained_amount = neutral_transacted_amount - overnight_position
        ###########remained_amount#########

        profit_and_loss_times_dict = {'max_profit_times':max(profit_times_list), 'max_profit_positions':max(profit_positions_list), 'max_loss_times':max(loss_times_list), 'max_loss_positions':max(loss_positions_list), 'remained_amount':int(remained_amount)}
        return profit_and_loss_times_dict

    else:
        return None

if __name__ == '__main__':
    Futu_api = futu_Api()
    print(Futu_api.get_market_snapshot('13068'))

