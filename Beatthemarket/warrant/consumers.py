import asyncio
from time import sleep
from asgiref.sync import SyncToAsync, async_to_sync, sync_to_async

from channels.generic.websocket import AsyncJsonWebsocketConsumer, WebsocketConsumer
from channels.db import database_sync_to_async
# from channels.layers import get_channel_layer

from django.db.models.query import QuerySet
from django.utils import timezone
from django.db.models import Max, Min
from django.forms.models import model_to_dict
from django.db.models import Q

from datetime import date, datetime, timedelta

from pandas.core.arrays import boolean
from math import e
from os import replace
# from metrics.models import *
import talib, random, threading
import mplfinance as mpf
import numpy as np
from tqdm.asyncio import tqdm
from warrant.views import *

class WarrantConsumer(AsyncJsonWebsocketConsumer):
    TIMES_REMAIN_API_SUBS = 0
    TIMES_GET_CAPITAL_FLOW = 30
    TIMES_GET_CAPITAL_DISTRIBUTION = 30

    IGNORE_LOW_VOLATILITY = 10
    VOLUME_PERIOD_COMPARE = 3
    VOLUME_MULTIPLIER = 5
    FROM_DAY_HIGH = 1
    FROM_DAY_LOW = 1
    FLAT_POSITION = 4

    async def connect(self):       
        print('------connect')
        self.room_group_name = 'event'
        self.Futu_Api = futu_Api()
        await (self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, *args, **Kwargs):
        print('------disconnect')
        await (self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        # await self.disconnect()

    async def send_message(self, content, *args , **kwargs):
        print('------send_message')
        await self.send_json({
            "msg_type":"update",
            "data" : content,
        })

    async def receive_json(self, data):
        print('------receive_message')
        content  = ''
        location = ''
        info     = ''
        if 'real_time_stock' in data:
            content = data['real_time_stock']
            location = 'real_time_stock'
        if 'message' in data:
            if 'warrantStreetMonitorFind' in data['message']:
                exDict_list, info = await asyncio.create_task( self.actual_warrant(data['wrtCode']) )
                exDict_list = exDict_list.to_dict('records')
                content = exDict_list
                location = 'warrantStreetMonitorFind'
            if 'warrantRecommendRefresh' in data['message']:
                content = await Get_wrt_mkt_closed_db.wrt_recommend()
                location = data['message']
            if 'stockSignalStart' in data['message']:
                asyncio.create_task( self.Process_data_routine() ) 
                asyncio.create_task( self.get_data_routines() )
            if 'stockSignalStop' in data['message']:
                tasks = asyncio.all_tasks()
                for task in tasks:
                    task.cancel()
                self.Futu_Api.close()
            if 'warrantRecommendGrabHistory' in data['message']:
                asyncio.create_task( self.Grab_Warrant_Historys() ) 
            if 'stockSignalSettings' in data['message']:
                asyncio.create_task( self.test() ) 
            if 'stockSignalRearrange' in data['message']:
                asyncio.create_task( self.Grab_Warrant_Historys() )
                # asyncio.create_task( self.hk_warrant_delete_suspended_wrt() )
                # asyncio.create_task( self.test() )

                # exDict_code_list = await get_DB.hk_stock_all_with_warrant_list()
                # accessable_wrt_lists = await self.Street_Hunters(exDict_code_list)

                # snapshot_df= []
                # start = datetime.today()
                # for accessable_wrt_list in accessable_wrt_lists:
                #     snapshot_df.append( asyncio.create_task( asyncio.coroutine( self.Futu_Api.get_market_snapshot(accessable_wrt_list) )) )
                # asyncio.gather(*snapshot_df)
                # end = datetime.today()
                # print(start-end)

                # print(accessable_wrt_lists[0])
                # snapshot_df = self.Futu_Api.get_market_snapshot(accessable_wrt_lists[0])
                # stocks_dict = snapshot_df[snapshot_df['stock_owner'].isnull()].to_dict(orient='records') # To find all stock df and turn it to dict
                # asyncio.create_task( self.get_stock_data_routine_bulk(stocks_dict) )
                # current_time = time_control()
                # asyncio.create_task( self.Clean_duplicate_warrant([current_time-timedelta(hours=9), current_time]) ) #! Warning if -1 will be 0 bid 0 ask and check stock bid ask is diff?
                # asyncio.create_task( self.Stock_rearrange() )
                # asyncio.create_task( self.actual_warrant('15974') )
                # asyncio.create_task( self.plot_graph('00388') )

                # start = datetime.today()
                codes = await get_DB.hk_stock_all_with_warrant_list()
                # codes_df = self.Futu_Api.get_market_snapshot(codes)
                # await futu_to_db(db_model=['hk_stock_timescale_bulk'], obj=codes_df)
                # codes = ['00700','03690','09988','00388','02382','01211','00388','02269']
                # list = []
                # for stock_code in codes:
                #     print(stock_code)
                #     stock_dict = await get_DB.hk_stock_timescale( code=stock_code, time__range=[time_control() - timedelta(minutes=10), time_control()])  # No data when hours=9
                #     if stock_dict:
                #         stock_spread = stock_dict['price_spread']
                #         # ! fix when no warrant market closed data
                #         warrant_df = await Get_wrt_mkt_closed_db.wrt_code_converstion_delta(code=stock_code, time__range=[time_control() - timedelta(days=5), time_control()])
                #         print(warrant_df)
                #         if not warrant_df.empty:
                #             warrant_df = warrant_df[(warrant_df['wrt_type'] == 'BULL') | (warrant_df['wrt_type'] == 'BEAR')]
                #             # warrant_df = warrant_df[(warrant_df['wrt_issuer_code'] == 'SG')]
                #             try:
                #                 warrant_df['wrt_sensitivity'] = abs( round( stock_spread / (warrant_df['wrt_conversion_ratio'] * warrant_df['price_spread']), 3 ) )
                #                 warrant_df = warrant_df[warrant_df['wrt_sensitivity'] > 1.9]
                #             except:
                #                 print('wrong', stock_code)

                #             if not warrant_df.empty:
                #                 # print(warrant_df)
                #                 list = list + warrant_df['code'].tolist()
                #     else:
                #         print(stock_dict)
                


                # print(list)
                # print(datetime.today() - start)
                # print(len(list))

                asyncio_tasks = []
                for stock_code in codes:
                    # print(stock_code)       
                # # #     asyncio.create_task( self.Warrant_monitor(i) )
                # #     # asyncio.create_task( self.plot_graph(stock_code) )

                    asyncio_tasks.append( asyncio.create_task( self.Grab_history_stock_data(stock_code=str(stock_code), num=400) ) )
                    pass
        else:
            content = data
            location = ''

        await self.channel_layer.group_send(
            'event',
            {
                "type": "send.message",
                'content': content,
                'info': info,
                "location": location
            }
        )

    # Main Layer

    async def Process_data_routine(self): # Stock_signal, Search_warrant
        print('Start Stock Signal')
        stock_codes = await get_DB.hk_stock_all_with_warrant_list()
        self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
        warrant_settings = await get_DB.warrant_settings()

        while True:
            stocks_snapshot_df = self.Futu_Api.get_market_snapshot(['HK.' + stock_code for stock_code in stock_codes])
            stock_codes_list = [code[3:] for code in stocks_snapshot_df['code'].unique()]
            start = datetime.today()
            current_time = time_control()
            exDict_list = []

            # # Get Stocks Signals
            stocks_signals_start = datetime.today()
            df = await Get_hk_stock_timescale_db.all_history(
                stock_codes_list, 
                time__range=[current_time - timedelta(days=4), current_time]
                )
            stock_codes_list = df['code'].unique()
            grouped = df.groupby(df.code)

            stocks_signals_start2 = datetime.today()
            for stock_code in stock_codes_list:
                stock_df = grouped.get_group(stock_code)
                exDict =  await self.Stock_signal(
                    stock_code               = stock_code, 
                    stock_data               = stocks_snapshot_df[stocks_snapshot_df['code'] == 'HK.' + stock_code].to_dict('records')[0], 
                    warrant_settings         = warrant_settings,
                    df                       = stock_df
                    )
                if exDict:
                    exDict_list.append(exDict)

            # exDict_list = await asyncio.gather(*exDict_list)
            exDict_list = [i for i in exDict_list if i] # Data have none
            exDict_df = pd.DataFrame(exDict_list)
            exDict_code_list = [i['Stock Code'] for i in exDict_list]

            # # Find Signal With Day High and put in the front
            day_high_code_list = [i['Stock Code'] for i in exDict_list if 'Day High' in i['Signal Type']]
            exDict_code_list = [x for x in exDict_code_list if x not in day_high_code_list]
            random.shuffle(exDict_code_list)
            exDict_code_list = day_high_code_list + exDict_code_list

            # Get Warrant Data
            warrant_signals_start = datetime.today()
            selected_warrants = await asyncio.create_task( 
                self.Search_warrant(
                    stock_codes_list = exDict_code_list
                    ) )
            if isinstance(selected_warrants, pd.DataFrame):
                if not selected_warrants.empty:
                    UniqueNames = selected_warrants.stock_owner.unique()
                    sele = []
                    for elem in UniqueNames:
                        sele.append( {'Stock Code':elem, 'warrant':selected_warrants[selected_warrants['stock_owner'] == elem].to_dict('records')[:9]} )
                    sele = pd.DataFrame(sele)
                    exDict_df = pd.merge(left=exDict_df, right=sele, left_on='Stock Code', right_on='Stock Code')

                exDict_list = exDict_df.to_dict(orient='records')
                print('Send Data To FrontEnd')
                await (self.channel_layer.group_send)(
                    'event', 
                    {
                        'type':'receive.json', 
                        'data': {
                            'real_time_stock': exDict_list,
                        }
                    })

            end = datetime.today()
            print(
                    'All', datetime.today() - start, 
                    'Stocks_signals_start', warrant_signals_start - stocks_signals_start,
                    'Stocks_signals_start', stocks_signals_start2 - stocks_signals_start,
                    'Warrant_signals_start', end - warrant_signals_start,  
                )
            while True:
                end = datetime.today()
                if end.second in [0, 1]: # Restrict time to 59 seconds
                    break                         
                if int((end - start).total_seconds()) < 60:
                    await asyncio.sleep(1)
                else:
                    break
            print('*******************')
            if end.hour == 16 and end.minute == 10:
                break

    async def get_data_routines(self): # Street_Hunters, get_stock_data_routine, get_wrt_data_routine
        print('Start Get Data Routines')
        # Handle Time lap for debug
        current_time = time_control()
        exDict_code_list2 = []
        get_data_routine_tasks = []
        warrant_signals_start = datetime.today()
        exDict_code_list = await get_DB.hk_stock_all_with_warrant_list()
        accessable_wrt_lists = await self.Street_Hunters(exDict_code_list)

        while True:
            routines_start = datetime.today()
            exDict_code_list2 += exDict_code_list
            random.shuffle(accessable_wrt_lists)

            # TODO if currenttime in [9-16]
            # Get All Data To DB
            for accessable_wrt_list in accessable_wrt_lists:
                current_time = time_control()
                snapshot_df = self.Futu_Api.get_market_snapshot(accessable_wrt_list) # Futu needs 10 seconds to get all lists
                stocks_dict = snapshot_df[snapshot_df['stock_owner'].isnull()].to_dict(orient='records') # To find all stock df and turn it to dict
                for stock_dict in stocks_dict:
                    # Inject Stock Data and avoid duplicate
                    if stock_dict['code'][3:] in exDict_code_list2:
                        exDict_code_list2.remove(stock_dict['code'][3:])
                        get_data_routine_tasks.append( asyncio.create_task( self.get_stock_data_routine(stock_dict) ) )
                # Inject Warrant Data
                get_data_routine_tasks.append( asyncio.create_task( self.get_wrt_data_routine(stocks_dict,snapshot_df,current_time) ) )

            await asyncio.gather(*get_data_routine_tasks)
            # Set Get Data Timer
            end = datetime.today()
            print('This Process cost:', 
                    round( (end-routines_start).total_seconds(), 2), 'Seconds ', 
                )
            print('The Time Now: ', end)
            self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
            self.TIMES_GET_CAPITAL_DISTRIBUTION = 30
            self.TIMES_GET_CAPITAL_FLOW = 30
            print('You Still Have Remain API Subs: ', self.TIMES_REMAIN_API_SUBS )
            # print('Total Signals: ', Total_signals)
            # print('Total exDict Signals (With Warrants): ', len(exDict_list))

            warrant_settings = await get_DB.warrant_settings()
            exDict_code_list2 = []

            while True:
                end = datetime.today()
                if end.second in [0, 1]: #Restrict time to 59 seconds
                    break                         
                if int((end - routines_start).total_seconds()) < 60:
                    await asyncio.sleep(1)
                else:
                    break
            print('*******************')
            if end.hour == 16 and end.minute == 10:
                asyncio.create_task( self.Grab_Warrant_Historys() )
                codes = await get_DB.hk_stock_all_with_warrant_list()
                asyncio_tasks = []
                for stock_code in codes:
                    asyncio_tasks.append( asyncio.create_task( self.Grab_history_stock_data(stock_code=str(stock_code), num=400) ) )
                asyncio.sleep(10000)

    async def actual_warrant(self, warrant_code):
        current_time                             = time_control()
        info = {}
        warrant_df                               = await Get_hk_wrt_timescale_db.history(code=warrant_code, time__range=[current_time-timedelta(hours=9), current_time])
        if not warrant_df.empty:
            warrant_df['time']                   = warrant_df['time'].dt.tz_convert('Asia/Hong_Kong')
            warrant_df['stock_bid_ratio']        = round( warrant_df['stock_bid_vol'] / (warrant_df['stock_ask_vol'] + warrant_df['stock_bid_vol']), 2)
            warrant_df['stock_ask_ratio']        = round( warrant_df['stock_ask_vol'] / (warrant_df['stock_ask_vol'] + warrant_df['stock_bid_vol']), 2)
            warrant_df['stock_spread']           = round( (warrant_df['stock_ask_price'] - warrant_df['stock_bid_price']) / warrant_df['stock_price_spread'], 0)
            warrant_df                           = warrant_df[warrant_df['stock_spread'] == 1]
            warrant_df                           = warrant_df.reset_index(drop=True)

            if not warrant_df.empty:
                first_valid_no                   = warrant_df[(warrant_df.bid_price.astype(float) != float(0)) & (warrant_df.ask_price.astype(float) != float(0))].first_valid_index()

                info                             = {'code':warrant_df['code_id'].iloc[-1], 'wrt_sen':warrant_df['wrt_sensitivity'].iloc[-1]}
                first_bid                        = warrant_df['bid_price'][first_valid_no]
                first_ask                        = warrant_df['ask_price'][first_valid_no]
                first_price_spread               = warrant_df['price_spread'][first_valid_no]
                stock_first_bid                  = warrant_df['stock_bid_price'][first_valid_no]
                stock_first_ask                  = warrant_df['stock_ask_price'][first_valid_no]

                # Same wrt_price and stock_price situation
                warrant_df_ask                   = warrant_df[
                                                                (warrant_df['stock_ask_price'] == warrant_df.iloc[-1]['stock_ask_price']) 
                                                            ]
                wrt_price_in_same_price = warrant_df_ask['ask_price'].unique()
                if len(wrt_price_in_same_price) > 1: # More than 1 wrt_price in same stock price
                    warrant_df_ask                   = warrant_df_ask[
                                                                    (warrant_df['ask_price'] == wrt_price_in_same_price.min())
                                                                ]
                    info['ask_high_low_suggest']     = wrt_price_in_same_price.min()
                else:
                    warrant_df_ask                   = warrant_df_ask[
                                                                    (warrant_df['ask_price'] == warrant_df.iloc[-1]['ask_price'])
                                                                ]

                warrant_df_bid                   = warrant_df[
                                                                (warrant_df['stock_bid_price'] == warrant_df.iloc[-1]['stock_bid_price']) 
                                                            ]
                wrt_price_in_same_price = warrant_df_bid['bid_price'].unique()
                if len(wrt_price_in_same_price) > 1: # More than 1 wrt_price in same stock price
                    warrant_df_bid                   = warrant_df_bid[
                                                                    (warrant_df['bid_price'] == wrt_price_in_same_price.max())
                                                                ]
                    info['bid_high_low_suggest']     = wrt_price_in_same_price.max()
                else:
                    warrant_df_bid                   = warrant_df_bid[
                                                                (warrant_df['bid_price'] == warrant_df.iloc[-1]['bid_price'])
                                                                ]

                info['bid_ratio_suggest']        = warrant_df_bid['stock_bid_ratio'].min()
                info['bid_vol_suggest']          = warrant_df_bid['stock_bid_vol'].min()

                info['ask_ratio_suggest']        = warrant_df_ask['stock_ask_ratio'].min()
                info['ask_vol_suggest']          = warrant_df_ask['stock_ask_vol'].min()
                # Same wrt_price and stock_price situation


                warrant_df['stock_bid_move']     = round( (warrant_df['stock_bid_price'] - stock_first_bid) / (warrant_df['stock_price_spread']), 4)
                warrant_df['stock_ask_move']     = round( (warrant_df['stock_ask_price'] - stock_first_ask) / (warrant_df['stock_price_spread']), 4)

                #! When ask bid not 0 # bug stock_bid == stock_ask ???
                warrant_df['estimated_bid']      = round( first_bid + warrant_df['stock_bid_move'] * first_price_spread * warrant_df['wrt_sensitivity'], 4 )
                warrant_df['is_normal']          = round( warrant_df['bid_price'] - warrant_df['estimated_bid'], 4)

                warrant_df                       = warrant_df.drop(['update_time', 'id' ,'price_spread' ,'stock_owner_id' ,'code_id'], axis=1)
                warrant_df['time']               = warrant_df['time'].dt.strftime("%H:%M")
                return warrant_df.iloc[::-1], info
        return pd.DataFrame(None), info

    # Second Layer

    async def Stock_signal(self, stock_code, stock_data, warrant_settings, df=None): # Grab_history_stock_data, Signal_above_MA
        if not df.empty:
            day_high = df['high_price'].max()
            day_low  = df['low_price'].min()

        # Data Cleaning
        df = df.set_index('time')
        df.index = pd.to_datetime(df.index, format='%Y-%m-%d %H:%M:%S')
        output = df.sort_index()
        output = df.resample('3T', closed = 'right',label = 'right').agg({'last_price': 'last', 'volume': 'sum', 'open_price':'first', 'high_price':'max','low_price':'min'})
        output = output.fillna(method='ffill')  # Fill NAN Objects with forward Objecs

        # Inject data to exDict
        exDict = {'Stock Code':stock_code}
        exDict['Ask Price']  = stock_data['ask_price']
        exDict['Bid Price']  = stock_data['bid_price']

        if day_low:
            exDict['Price Change'] = round( (stock_data['last_price'] - day_low) / day_low * 100 , 2 )
            # if hk_stock_dict:
            exDict['Price Change Points From Day Low'] = round( (stock_data['last_price'] - day_low) / stock_data['price_spread'] , 0 )
            if exDict['Price Change Points From Day Low'] < 0:
                exDict['Price Change Points From Day Low'] = 0
            exDict['Price Change Points From Day High'] = round( (day_high - stock_data['last_price']) / stock_data['price_spread'] , 0 )
            if exDict['Price Change Points From Day High'] < 0:
                exDict['Price Change Points From Day High'] = 0
            if exDict['Price Change Points From Day High'] + exDict['Price Change Points From Day Low'] < self.IGNORE_LOW_VOLATILITY:
                return None
        # else:
                exDict['Price Change Points'] = ''
        exDict['Day High'] = day_high
        exDict['Day Low'] = day_low
        exDict['Current Price'] = stock_data['last_price']

        # Technical Analysis
        EMA_5 = await self.Signal_above_MA(timeperiod=5, df=output)
        EMA_10 = await self.Signal_above_MA(timeperiod=10, df=output)
        EMA_20 = await self.Signal_above_MA(timeperiod=20, df=output)
        EMA_60 = await self.Signal_above_MA(timeperiod=60, df=output)
        EMA_120 = await self.Signal_above_MA(timeperiod=120, df=output)

        past_3_volume = output.iloc[-self.VOLUME_PERIOD_COMPARE:]['volume'].sum()
        past_3_to_6_volume = output.iloc[-self.VOLUME_PERIOD_COMPARE*2:-self.VOLUME_PERIOD_COMPARE]['volume'].sum()

        exDict['Signal Type'] = []
        # if await self.Signal_Ranking(code=stock_code, df=stock_data, hk_stock_timescale_db=hk_stock_timescale_db):
        #     exDict['Signal Type'] = exDict['Signal Type'] + 'Rank.CH'
        # if await self.Signal_volume_extreme(stock_code=stock_code, period=11):
        #     exDict['Signal Type'].append('Vol.CH')
        # if stock_data['last_price']> EMA_10 > EMA_20 > EMA_60 > EMA_120:
        #     exDict['Signal Type'].append('Uptrend')
        if stock_data['last_price'] > EMA_5 > EMA_10 > EMA_20 > EMA_60 > EMA_120:
            exDict['Signal Type'].append('Uptrend***')
        if EMA_5 > stock_data['last_price'] > EMA_10 > EMA_20 > EMA_60 > EMA_120:
            exDict['Signal Type'].append('Uptrend**')
        # print(type(stock_data['price_spread']))
        if EMA_20 > EMA_60 > EMA_120 and ( EMA_20 + stock_data['price_spread'] > stock_data['last_price'] >  EMA_20 - stock_data['price_spread']):
            exDict['Signal Type'].append('UptrendMA')
        if EMA_10 > stock_data['last_price'] > EMA_20 > EMA_60 > EMA_120: ####
            exDict['Signal Type'].append('Uptrend*')
        if EMA_120 > EMA_60 > EMA_20 > stock_data['last_price']:
            exDict['Signal Type'].append('Downtrend')

        if 'Price Change Points From Day High' in exDict:
            if exDict['Price Change Points From Day High'] < self.FROM_DAY_HIGH:
                exDict['Signal Type'].append('Day High')
        if 'Price Change Points From Day Low' in exDict:
            if exDict['Price Change Points From Day Low'] < self.FROM_DAY_LOW:
                exDict['Signal Type'].append('Day Low')

        if (past_3_volume - past_3_to_6_volume) / past_3_to_6_volume > 20:
            exDict['Signal Type'].append('Ext.Volume.CH')
            # print(stock_code)
            # print(output.iloc[-self.VOLUME_PERIOD_COMPARE:])
            # print('past_3_volume', past_3_volume)
            # print('past_3_to_6_volume', past_3_to_6_volume)
        elif (past_3_volume - past_3_to_6_volume) / past_3_to_6_volume > self.VOLUME_MULTIPLIER:
            exDict['Signal Type'].append('Volume.CH')

        # Restricted by API limit
        # if self.TIMES_GET_CAPITAL_DISTRIBUTION > 10:
        #     if await self.Signal_capital_distribution(stock_code=stock_code):
        #         exDict['Signal Type'].append('All Inflow ')
        #         self.TIMES_GET_CAPITAL_DISTRIBUTION -= 1

        # print(self.Futu_Api.get_capital_distribution('HK.' + stock_code))
        # # print(self.REMAIN_API_SUBS)
        # # if self.REMAIN_API_SUBS > 1:
        # # if stock_code == '03993':
        # data = self.Futu_Api.get_capital_flow('HK.' + stock_code)
        # data['capital_flow_item_time'] = pd.to_datetime(data['capital_flow_item_time'])
        # data.capital_flow_item_time = data.capital_flow_item_time.dt.tz_localize('UTC').dt.tz_convert('Asia/Hong_Kong') - timedelta(hours=8)
        # data = data.set_index('capital_flow_item_time')
        # data = data.resample('3min').agg({'in_flow':'last'})
        # data = data.between_time('13:01', '11:59')   #HK Lunch Hour No DATA!!!!
        # data = data['in_flow'].diff()
        # data = data.fillna(0)

        # output = output['last_price'].diff()

        # result = pd.concat([data, output], axis=1).reindex(data.index)
        # with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        #     print(result)

        # # final = pd.DataFrame({'time'},{'data'})
        # # for i in range(11,len(result)):
        # #     time = result.index.values[i]
        # #     data1 = result[i-10:i].corr(method ='pearson')['last_price']['in_flow']
        # #     final = final.append({'time':time, 'data':data1}, ignore_index=True)
        # #     # print(final)
        # #     # final.append(pd.DataFrame({"time":[result.index.values[i]],"value":result[:i].corr(method ='pearson')['last_price']['in_flow']}))
        # # final.time = final.time.dt.tz_localize('UTC').dt.tz_convert('Asia/Hong_Kong')
        # # final = final.set_index('time')
        # # with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        #     # print(final)
        # self.REMAIN_API_SUBS-= 1

        # if set(['Up trend'] ).issubset(exDict['Signal Type']):

        check_list = warrant_settings
        isinchecklist = [i for i in exDict['Signal Type'] if i in check_list]
        if isinchecklist:
            return exDict

            #TODO Retracement Reversal Breakout Cosolitation / Large Scale Order

    async def Search_warrant(self, stock_codes_list:list) -> pd.DataFrame:
        current_time = time_control()
        start = datetime.today()
        random.shuffle(stock_codes_list)

        stock_codes_list = stock_codes_list[:30]
        wrt_codes_df = await Get_hk_wrt_db.all_code_converstion_delta(stock_codes_list=stock_codes_list)

        start2 = datetime.today()
        wrt_dfs = await Get_hk_wrt_timescale_db.all_history_by_stock_owner(stock_codes_list, [current_time-timedelta(hours=10), current_time])
        wrt_df = wrt_dfs.drop_duplicates(subset=['code_id'], keep='last')

        if not wrt_df.empty:
            wrt_df = pd.merge(left=wrt_df, right=wrt_codes_df, left_on='code_id', right_on='code')
            

        start3 = datetime.today()
        if not wrt_df.empty:
            wrt_df['flat_position'] = round( ((wrt_df['ask_price'] - wrt_df['bid_price']) / wrt_df['price_spread'] )/ wrt_df['wrt_sensitivity'], 1)
            selected_series = wrt_df[((wrt_df['wrt_sensitivity'] == 0.4) | (wrt_df['wrt_sensitivity'] == 0.5)) & (wrt_df['flat_position'] <= 2.5)]
            wrt_df = wrt_df.drop(['update_time','id','time','price_spread','wrt_sensitivity'], axis=1)
            wrt_df = wrt_df[wrt_df['bid_price'] > 0]
            wrt_df = wrt_df[0 < wrt_df['flat_position']]
            wrt_df = wrt_df[wrt_df['flat_position'] < 20]
            wrt_df = wrt_df.sort_values(by=['flat_position'])
            wrt_df = wrt_df.set_index('code')
            wrt_df = wrt_df[wrt_df['flat_position'] < self.FLAT_POSITION]
            wrt_df['code'] = wrt_df.index
            wrt_df['xyaaa'] = wrt_df['code'].map(selected_series.set_index('code')['flat_position'],  na_action='ignore')

            with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
                print(wrt_df)
            
            wrt_df = wrt_df.rename(columns={'stock_owner_id': 'stock_owner'})

            end = datetime.today()
            print(
                'Search Wrt: ',
                'First', (start2 - start).total_seconds(), 
                'Second', (start3 - start2).total_seconds(), 
                'Third', (end - start3).total_seconds(), 
                'Len', len(stock_codes_list))
            if not wrt_df.empty:
                return wrt_df

    async def Street_Hunters(self, stock_code_list) -> list:
        current_time = time_control()
        warrant_code_list_to_futu = []
        warrant_codes_list = []

        for stock_code in stock_code_list:
            warrant_code_list = []
            stock_qs = await get_DB.hk_stock(code=stock_code)
            warrant_code_df = await Get_wrt_mkt_closed_db.wrt_code_converstion_delta(
                                                stock_owner=stock_qs, 
                                                time__range=[current_time - timedelta(days=4), current_time],   #TODO long holiday fix it
                                                )

            try: # When Stock has no match warrant
                warrant_code_df = warrant_code_df[warrant_code_df['last_price'] > 0.019]
                warrant_code_list.append(stock_code) # Add back stock code
                warrant_code_list = warrant_code_list + warrant_code_df['code'].tolist()
                warrant_code_list = list(set(warrant_code_list)) # To remove duplicate due to timedelta not stable
            except:
                print('warrant_codes_df not found ' , stock_code)

            total_warrant_code_len = len( warrant_codes_list + warrant_code_list ) 
            if total_warrant_code_len > 400:
                warrant_code_list_to_futu.append( warrant_codes_list + warrant_code_list[: len(warrant_code_list) - (total_warrant_code_len - 400)] )
                warrant_codes_list = []
                warrant_code_list = [stock_code] + warrant_code_list[len(warrant_code_list) - (total_warrant_code_len - 400):]

                for i in range( 0 , math.ceil(len(warrant_code_list)/400) ):
                    if i == 0:
                        if len(warrant_code_list) > 400:
                            warrant_code_list_to_futu.append( warrant_code_list[:400] )
                    else:
                        if len( warrant_code_list ) < 400:
                            warrant_codes_list = [stock_code] + warrant_code_list[400:]
                        else:
                            warrant_code_list_to_futu.append([stock_code] + warrant_code_list[:399])
                            warrant_code_list = [stock_code] + warrant_code_list[399:]

            warrant_codes_list = warrant_codes_list + warrant_code_list

        warrant_code_list_to_futu.append(warrant_codes_list)
        return warrant_code_list_to_futu

    async def get_stock_data_routine(self, stock_dict):
        current_time = time_control()
        # Inject Data To DB
        stock_kline_df = self.Futu_Api.get_cur_kline(stock_dict['code'])
        stock_kline_dict_list = stock_kline_df.to_dict('records')
        try:
            # Real-Time Data too early
            if current_time.hour == 16 and current_time.minute > 0: # TODO auto check missing data
                asyncio.create_task( futu_to_db(stock_dict['code'], stock_kline_dict_list[-1], 'hk_stock_timescale', stock_dict=stock_dict) )
                asyncio.create_task( futu_to_db(stock_dict['code'], stock_kline_dict_list[-2], 'hk_stock_timescale', stock_dict=stock_dict) )
                asyncio.create_task( futu_to_db(stock_dict['code'], stock_kline_dict_list[-3], 'hk_stock_timescale', stock_dict=stock_dict) )
            else:
                if len(stock_kline_dict_list) < 2:
                    print(stock_dict)
                    print(stock_kline_dict_list)
                else:
                    asyncio.create_task( futu_to_db(stock_dict['code'], stock_kline_dict_list[-2], 'hk_stock_timescale', stock_dict=stock_dict) )
        except AttributeError:
            print('Futu to DB Error', stock_kline_dict_list)

    async def get_wrt_data_routine(self, stocks_dict, snapshot_df, current_time):
        for stock_dict in stocks_dict:
            warrant_df = snapshot_df[snapshot_df['stock_owner'] == stock_dict['code']]
            warrant_df = warrant_df[['code','update_time', 'ask_vol', 'ask_price', 'bid_price','bid_vol','wrt_conversion_ratio','wrt_delta', 'price_spread','stock_owner','wrt_type','wrt_issuer_code']]
            warrant_df['wrt_sensitivity'] = abs( round( (stock_dict['price_spread'] * warrant_df['wrt_delta']) / (warrant_df['wrt_conversion_ratio'] * warrant_df['price_spread']), 3 ) )
            warrant_df['flat_position'] = round( ((warrant_df['ask_price'] - warrant_df['bid_price']) / warrant_df['price_spread'] )/ warrant_df['wrt_sensitivity'], 1)
            warrant_df = warrant_df[warrant_df['code'] != stock_dict['code']] # Exclude Stock Dict

            stock_dict['obj'] = warrant_df
        # print(len(stocks_dict), [stock_dict['code'] for stock_dict in stocks_dict])
        asyncio.create_task( futu_to_db(db_model=['hk_warrant_timescale_bulk'], stocks_dict=stocks_dict,current_time=current_time) )

    # Signals Type

    async def Signal_capital_distribution(self, stock_code):
        df = self.Futu_Api.get_capital_distribution('HK.' + stock_code)
        if df.iloc[0]['capital_in_big'] > df.iloc[0]['capital_out_big'] and df.iloc[0]['capital_in_mid'] > df.iloc[0]['capital_out_mid'] and df.iloc[0]['capital_in_small'] > df.iloc[0]['capital_out_small'] :
            return True

    async def Signal_above_MA(self, timeperiod, df):
        output = np.array(df['last_price'])
        output = output[~np.isnan(output)]
        output = talib.EMA(output, timeperiod=timeperiod)
        return output[-1]

    async def Signal_volume_extreme(self, stock_code, period, VOLUME_MULTIPLIER=3):
        # Check Volume Extreme
        diff_voluem_muliplier = await cal_volume_extreme(code=stock_code, num_data=period)
        if diff_voluem_muliplier:
            if diff_voluem_muliplier > VOLUME_MULTIPLIER:
                return 'Volume Change'

    async def Signal_Ranking(self, code, df, hk_stock_timescale_db):
        # Check Increase Ranking
        if hk_stock_timescale_db:
            percentage_change = (df['last_price'] - hk_stock_timescale_db['last_price']) / hk_stock_timescale_db['last_price']
            if percentage_change != 0:
                if (percentage_change > 1.05 or percentage_change < 0.95):
                    return 'Signal Ranking Change'

    async def Signal_restrict(self):
        #日線阻力位
        pass

    async def Signal_BOLL(self):
        #BOLL通道突破
        pass

    async def Signal_Low_High_volume(self):
        #低位大成交
        pass

    # Grab History Data Types

    async def Grab_Warrant_Historys(self): # Grab_Warrant_History_all_check_list, Grab_Warrant_History, Grab_history_stock_data
        print('Grab Warrant History')

        codes = await get_DB.hk_stock_all_with_warrant_list()

        task_start_time = datetime.today()
        end_date = time_control()
        start_date = end_date - timedelta(hours=16)

        asyncio_tasks = []
        futu_warrant_check_list = []
        for code in tqdm(codes):
            futu_warrant_check_list += await self.Grab_Warrant_History_all_check_list(code, start_date=start_date)
            if len(futu_warrant_check_list) > 200: # Api Restricted to 200 numbers
                asyncio_tasks.append( asyncio.create_task( self.Grab_Warrant_History(futu_warrant_check_list[:200]) ) )
                futu_warrant_check_list = futu_warrant_check_list[200:]
            if code == codes[-1]: # The Last One
                asyncio_tasks.append( asyncio.create_task( self.Grab_Warrant_History(futu_warrant_check_list[:200]) ) )

            # ? Use When adjust
            # print(code)
            # warrant_codes_df = await Get_wrt_mkt_closed_db.wrt_mkt_closed_get_warrant_number(code=code, time__range=[end_date - timedelta(hours=9), end_date], current_time=end_date)
            # warrant_list = ['HK.' + d['code'] for d in warrant_codes_df]
            # print(warrant_list)
            # for warrant in warrant_list:
            #     if await Get_wrt_mkt_closed_db.get_wrt_vol(code=warrant['code'], time__range=[start_date, end_date]):
            #         print('getting ticker')
            #         self.Futu_Api.subscribe('HK.'+ warrant['code'], 'TICKER')
            #         warrant_rt_ticker = self.Futu_Api.get_rt_ticker('HK.'+ warrant['code'],)
            #         await futu_to_db(code=warrant['code'], obj=warrant_rt_ticker.to_dict(), db_model=['warrant_transaction'])
            #         self.Futu_Api.unsubscribe('HK.'+ warrant['code'],)         

        await asyncio.gather(*asyncio_tasks) # To wait until finished
        await pack_to_warrant_recommend(start_date=start_date, end_date=end_date)

        # Start Get Stock Data History
        asyncio_tasks = []
        codes = await get_DB.hk_stock_all_with_warrant_list()
        for code in codes:
            asyncio_tasks.append( asyncio.create_task( self.Grab_history_stock_data(stock_code= code) ) )
        await asyncio.gather(*asyncio_tasks) # To wait until finished

        print('Time Spent on Task', datetime.today() - task_start_time)

    async def Grab_Warrant_History_all_check_list(self, code, start_date): # To get latest warrant list
        futu_warrant_check_list = []
        if code:
            warrant_list = self.Futu_Api.get_warrant(stock_owner='HK.' + code, type_list=['CALL', 'PUT', 'BULL', 'BEAR'])
            for warrant in warrant_list['stock']:
                if not await Get_wrt_mkt_closed_db.wrt_mkt_cl( 
                                            code=warrant[3:], 
                                            time__range=start_date
                                        ):
                    futu_warrant_check_list.append(warrant)
        return futu_warrant_check_list

    async def Grab_Warrant_History(self, futu_warrant_check_list):
        warrant_list = self.Futu_Api.get_market_snapshot(futu_warrant_check_list)
        for index, warrant_dataframe in warrant_list.iterrows():
            warrant_dict = warrant_dataframe.to_dict()
            await futu_to_db(code=warrant_dict['code'][3:], obj=warrant_dict, db_model=['warrant_market_closed'])

            if warrant_dict['volume'] != 0:
                self.Futu_Api.subscribe(warrant_dict['code'], 'TICKER')
                warrant_rt_ticker = self.Futu_Api.get_rt_ticker(warrant_dict['code'], ignore_error=True)
                await futu_to_db(code=warrant_dict['code'][3:], obj=warrant_rt_ticker.to_dict(), db_model=['warrant_transaction'])
                self.Futu_Api.unsubscribe(warrant_dict['code'])

    async def Grab_history_stock_data(self, stock_code, num=1000):
        print('Start Get Stock Data History')
        stock_dfs = self.Futu_Api.get_cur_kline('HK.'+ stock_code, num=num)
        stock_df_list = stock_dfs.to_dict('records')

        data_start = pytz.timezone('Asia/Hong_Kong').localize(datetime.strptime(stock_df_list[0]['time_key'], "%Y-%m-%d %H:%M:%S"))
        data_end   = pytz.timezone('Asia/Hong_Kong').localize(datetime.strptime(stock_df_list[-1]['time_key'], "%Y-%m-%d %H:%M:%S"))
        data_end   = data_end # + timedelta(minutes=10)

        await get_DB.hk_stock_timescale_delete(code=stock_code, time__range=[data_start, data_end])
        # print(datetime.today() - timedelta(days=10))
        # await get_database(db=['hk_stock_timescale_delete'] , code=stock_code, time__range=[datetime.today() - timedelta(days=10), datetime.today()])
        for stock_df in tqdm(stock_df_list):
            await futu_to_db(stock_code, stock_df, 'hk_stock_timescale')

    # Warrant Signals Type

    async def data_cleaning(self, last_price_list):
        # Data Cleaning
        output = pd.DataFrame(last_price_list)
        output['time'] = output['time'].dt.tz_convert('Asia/Hong_Kong')
        output = output.set_index('time')
        output = output[output.index.weekday < 5]  # Exclude Sat, Sun
        output = output.resample('3T', closed = 'right',label = 'right').agg({'open_price': 'first','high_price': 'max','low_price': 'min', 'last_price':'last','volume':'sum'})
        output = output.between_time('9:30', '16:00')   # HK Trading Hour
        output = output.between_time('13:00', '12:00')   # HK Lunch Hour
        output = output.fillna(method='ffill')  # Fill NAN Objects with forward Objecs
        return output

    async def plot_graph(self, stock_code):
        start = datetime.today()
        current_time = time_control()
        last_price_df = await get_DB.hk_stock_timescale_all_history( 
                                            code=stock_code, 
                                            time__range=[current_time - timedelta(days=2), current_time], 
                                            current_time=current_time
                                            )
        last_price_df = await self.data_cleaning(last_price_df)
        last_price_df = last_price_df.rename(columns={'open_price':'Open', 'high_price':'High','low_price':'Low','last_price':'Close','volume':'Volume'}, index={'time':'Date'})
        print(last_price_df)

        integer = pd.DataFrame()
        integer['CDLENGULFING'] = talib.CDLENGULFING(last_price_df['Open'], last_price_df['High'], last_price_df['Low'], last_price_df['Close'])

        last_price_df['last_price'] = last_price_df['Close']

        open_mav3 = last_price_df["Open"].rolling(3).mean().values
        open_mav5 = last_price_df["Open"].rolling(5).mean().values
        open_mav10 = last_price_df["Open"].rolling(10).mean().values
        open_mav20 = last_price_df["Open"].rolling(20).mean().values

        change_point = last_price_df['Close'] - open_mav5
        last_price_df['change_point'] = (change_point < 0).astype(int)

        xd = []
        mark = (0,0,0) # mark[0] is number, mark[1] is 1 (high) 0 (low), mark[2] is value
        value = [0,0] # High, Low
        last_price_df_list = last_price_df.index.tolist()
        # print(last_price_df_list)
        for i in range(0, len(last_price_df['change_point'])):
            if i == len(last_price_df['change_point']) - 1:
                if mark[1] == 1:
                    xd.append(last_price_df.iloc[mark[0]:i]['High'].max())
                if mark[1] == 0:
                    xd.append(last_price_df.iloc[mark[0]:i]['Low'].min())
            else:
                if last_price_df.iloc[i]['change_point'] == 0 and last_price_df.iloc[i + 1]['change_point'] == 1: # Twist Point Get High
                    high_value = last_price_df.iloc[mark[0]:i]['High'].max()
                    low_value = last_price_df.iloc[mark[0]:i]['Low'].min()
                    if low_value < mark[2]: # Due to MA not robust adjust
                        print('low wrong')
                        print(last_price_df.iloc[mark[0]:i]['Low'].idxmin(), 'is lower')
                        len_no = last_price_df_list.index(last_price_df.iloc[mark[0]:i]['Low'].idxmin())
                        xd[len_no] = last_price_df.iloc[mark[0]:i]['Low'].min()

                    len_no = last_price_df_list.index(last_price_df.iloc[mark[0]:i]['High'].idxmax())
                    xd[len_no] = last_price_df.iloc[mark[0]:i]['High'].max()
                    xd.append(np.nan)
                    mark = (i,1,high_value)

                elif last_price_df.iloc[i]['change_point'] == 1 and last_price_df.iloc[i + 1]['change_point'] == 0: # Twist Point Get Low
                    high_value = last_price_df.iloc[mark[0]:i]['High'].max()
                    low_value = last_price_df.iloc[mark[0]:i]['Low'].min()
                    if high_value > mark[2]: # Due to MA not robust adjust
                        print('high wrong')
                        print(last_price_df.iloc[mark[0]:i]['High'].idxmax(), 'is Higher')
                        len_no = last_price_df_list.index(last_price_df.iloc[mark[0]:i]['High'].idxmax())
                        xd[len_no] = last_price_df.iloc[mark[0]:i]['High'].max()

                    len_no = last_price_df_list.index(last_price_df.iloc[mark[0]:i]['Low'].idxmin())
                    xd[len_no] = last_price_df.iloc[mark[0]:i]['Low'].min()
                    xd.append(np.nan)
                    mark = (i,0,low_value)
                else:
                    xd.append(np.nan)

        last_price_df['high_low'] = np.array(xd)
        print(last_price_df['high_low'])
        # last_price_df['high_low'] = last_price_df['high_low'].fillna(method='bfill')

        with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
            print(last_price_df)
        last_price_df.to_csv('123.csv')
        mavdf = pd.DataFrame(dict(OpMav10=open_mav10, OpMav5=open_mav5,OpMav20=open_mav20),index=last_price_df.index)
        ax = mpf.make_addplot(last_price_df['high_low'],type='scatter', color='green')
        ap = mpf.make_addplot(mavdf,type='line')
        mpf.plot(last_price_df,type='candle', volume=True ,savefig=f'chart//{stock_code}.png',addplot=[ap,ax])

        print('Time Consumes ', datetime.today() - start)

    async def Warrant_monitor(self, warrant_code):
        CHEKC_MINUTE_RANGE = 5

        current_time = datetime.today().replace(day=27, hour=10, minute=8)
        df = self.Futu_Api.get_rt_ticker('HK.' + warrant_code)
        BUY_df = df[(df['ticker_direction'] == 'BUY') & (df['turnover'] >= 100000) & (df['turnover'] <= 1000000)]

        with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
            print(BUY_df)

        if not BUY_df.empty:
            print(warrant_code)

            # BUY_df = BUY_df.set_index('time')
            # BUY_df.index=pd.to_datetime(BUY_df.index)      
            # BUY_df = BUY_df.between_time( 
            #     *pd.to_datetime([current_time - timedelta(minutes=CHEKC_MINUTE_RANGE), current_time]).time)
            # if not BUY_df.empty:
            #     return warrant_code

    async def Clean_duplicate_warrant(self, time__range):
        codes = await get_DB.hk_warrant_all_list()
        batch_size = 50
        for i in tqdm(range(0, math.ceil((len(codes) / batch_size))), total=math.ceil((len(codes) / batch_size))):
            batch = codes[i*batch_size:(i+1)*batch_size]
            asynic_tasks = []
            for code in batch:
                asynic_tasks.append( asyncio.create_task( Get_hk_wrt_timescale_db.delete_duplicated(code=code, time__range=time__range) ) )
            await asyncio.gather(*asynic_tasks)

    async def Clean_wrong_data(self):
        for i in range(10000, 100000):
            codes = await get_DB.hk_stock_all_with_warrant_list()

    async def hk_warrant_save_from_mkt_closed(self):
        wrt_codes = await Get_hk_wrt_db.all_code_list()
        print(len(wrt_codes))

        for wrt_code in tqdm(wrt_codes):
            print(wrt_code)
            wrt_dict = await Get_wrt_mkt_closed_db.latest(wrt_code)
            await Get_hk_wrt_db.update(code=wrt_code, wrt_dict=wrt_dict)

    async def hk_warrant_delete_suspended_wrt(self):
        current_time = time_control()
        wrt_codes = await Get_hk_wrt_db.all_code_list()
        print(len(wrt_codes))

        for wrt_code in tqdm(wrt_codes):
            # print(wrt_code)
            wrt_dict = await Get_wrt_mkt_closed_db.latest(wrt_code, [current_time-timedelta(days=1), current_time])
            if not wrt_dict:
                print( await Get_hk_wrt_db.delete(code=wrt_code) )

    async def test(self):
        x = _Time_control()
        print(x)
        print(_Time_control().current_time)
        print(_Time_control().time())
        print(_Time_control().is_trading_time())
        asyncio.sleep(1)
        print(x)
        print(_Time_control().current_time)
        print(_Time_control().time())
        print(_Time_control().is_trading_time())

    # Others

    async def get_stock_data_routine_bulk(self, stocks_dict: dict):
        current_time = time_control()
        stock_kline_dict_list=[]
        for stock_dict in stocks_dict:
            stock_kline_df = self.Futu_Api.get_cur_kline(stock_dict['code'])
            stock_kline_df['price_spread'] = stock_dict['price_spread']
            stock_kline_dict_list.append( stock_kline_df.to_dict('records') )

        asyncio.create_task( futu_to_db(obj = stock_kline_dict_list, db_model=['hk_stock_timescale_bulk']) )

    async def Stock_rearrange(self): # To rearrange stocks with warrants
        the_list =  await get_DB.hk_stock_all_with_warrant_list()
        other_list = ["00001","00002","00003","00004","00005","00006","00011","00012","00016","00017","00019","00027","00066","00101","00119","00123","00135","00144","00148","00151","00152","00168","00175","00189","00200","00241","00257","00267","00268","00270","00285","00288","00291","00293","00322","00323","00338","00347","00354","00358","00384","00386","00388","00390","00425","00486","00489","00493","00520","00522","00552","00636","00656","00669","00670","00688","00694","00696","00700","00708","00728","00753","00762","00763","00772","00778","00780","00788","00799","00813","00823","00836","00853","00857","00867","00868","00873","00880","00881","00883","00902","00909","00914","00916","00939","00941","00960","00966","00968","00981","00992","00998","01024","01038","01044","01055","01066","01088","01093","01099","01109","01113","01114","01128","01137","01138","01157","01171","01177","01186","01193","01209","01211","01268","01288","01299","01308","01313","01316","01336","01337","01339","01347","01359","01368","01378","01398","01458","01515","01516","01548","01558","01579","01610","01658","01691","01766","01772","01776","01787","01797","01800","01801","01810","01816","01818","01833","01876","01888","01896","01918","01919","01928","01929","01951","01958","01988","01995","01997","02007","02013","02015","02018","02020","02057","02186","02196","02202","02208","02238","02269","02282","02313","02318","02319","02328","02331","02333","02338","02342","02357","02359","02382","02388","02400","02500","02600","02601","02607","02628","02669","02688","02689","02727","02777","02799","02800","02822","02823","02828","02840","02866","02869","02883","02888","02899","03033","03067","03188","03311","03319","03320","03323","03328","03333","03347","03383","03606","03669","03690","03692","03759","03800","03868","03883","03888","03898","03908","03968","03969","03988","03993","03998","06030","06049","06060","06066","06078","06098","06110","06160","06169","06186","06618","06666","06690","06808","06837","06862","06865","06881","06886","06969","06993","09618","09626","09633","09698","09868","09888","09901","09922","09923","09926","09969","09988","09991","09992","09999"]

        output_list = sorted(set(other_list).difference(the_list))
        print(output_list)
        # for i in output_list:
        #     await get_DB.hk_stock_create_item(code=i)

    async def Warrant_timescale_handle(self, current_time, wrt_code_df, wrt_code): # Disposed
        try:
            try:
                wrt_dict = await Get_hk_wrt_timescale_db.history(code=wrt_code, time__range=[current_time - timedelta(hours=10), current_time], last=True)
            except: # is used to the open 10 minutes
                wrt_dict = await Get_hk_wrt_timescale_db.history(code=wrt_code, time__range=[current_time - timedelta(days=1), current_time], last=True)
        except:
            wrt_dict = None # Avoid no data
            # print('that warrant is new', wrt_code)

        if wrt_dict:
            wrt_dict['wrt_type'] = wrt_code_df['wrt_type'].values[0] # pd series value
            wrt_dict['wrt_issuer_code'] = wrt_code_df['wrt_issuer_code'].values[0]
        return wrt_dict

    async def Stock_signals_new(self): # Disposed
        print('Start Stock Signals')
        stock_codes = await get_DB.hk_stock_all_with_warrant_list()
        self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
        warrant_settings = await get_DB.warrant_settings()

        while True:
            # Get Futu Api Every 60s
            stocks_snapshot_df = self.Futu_Api.get_market_snapshot(['HK.' + stock_code for stock_code in stock_codes])
            start = datetime.today()
            exDict_list = []
            Street_Hunter_tasks = []

            if not stocks_snapshot_df.empty:   #To avoid error
                print(stocks_snapshot_df)

                # Get Stocks Signals
                stocks_signals_start = datetime.today()
                for i in range(0, len(stocks_snapshot_df)):
                    exDict = asyncio.create_task( self.Stock_signal(
                                                                    stock_code=stocks_snapshot_df.iloc[i].code[3:], 
                                                                    stock_data=stocks_snapshot_df.iloc[i].to_dict(), 
                                                                    warrant_settings=warrant_settings
                                                                ))
                    if exDict:
                        exDict_list.append(exDict)
                exDict_list = await asyncio.gather(*exDict_list)
                exDict_list = [i for i in exDict_list if i] # Data have none
                Total_signals = len(exDict_list)
                exDict_code_list = [i['Stock Code'] for i in exDict_list]

                # Find Signal With Day High and put in the front
                day_high_code_list = [i['Stock Code'] for i in exDict_list if 'Day High' in i['Signal Type']]
                exDict_code_list = [x for x in exDict_code_list if x not in day_high_code_list]
                random.shuffle(exDict_code_list)
                exDict_code_list = day_high_code_list + exDict_code_list

                # Get Warrant Data
                warrant_signals_start = datetime.today()
                for exDict_code in exDict_code_list[:30]:  # Should be to api
                    Street_Hunter_task = asyncio.create_task( self.Street_Hunter(stock_code=exDict_code) )
                    if Street_Hunter_task:
                        Street_Hunter_tasks.append(Street_Hunter_task)
                        # yield Street_Hunter_task

                selected_warrants = await asyncio.gather(*Street_Hunter_tasks)
                selected_warrants = [i for i in selected_warrants if i] # Data have none

                for exDict in exDict_list:
                    for selected_warrant in selected_warrants:
                        if exDict['Stock Code'] == selected_warrant[0]['stock_owner']:
                            exDict['warrant'] = selected_warrant
                exDict_list = [x for x in exDict_list if 'warrant' in x] #Drop Stock that have no warrant code

                # Send Signal to Websocket
                if exDict_list:
                    await (self.channel_layer.group_send)(
                        'event', 
                        {
                            'type':'receive.json', 
                            'data': {
                                'real_time_stock': exDict_list,
                            }
                        })

            # Set Get Data Timer
            end = datetime.today()
            print('This Process cost:', 
                    round( (end-start).total_seconds(), 2), 'Seconds ', 
                '(Stock Signals Cost:', 
                    round( (warrant_signals_start-stocks_signals_start).total_seconds(), 2),
                '/ ',
                'Warrant Signals Cost:',
                    round( (end-warrant_signals_start).total_seconds(), 2),
                ')',
                )
            print('The Time Now: ', end)
            self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
            self.TIMES_GET_CAPITAL_DISTRIBUTION = 30
            self.TIMES_GET_CAPITAL_FLOW = 30
            print('You Still Have Remain API Subs: ', self.TIMES_REMAIN_API_SUBS )
            print('Total Signals: ', Total_signals)
            print('Total exDict Signals (With Warrants): ', len(exDict_list))

            warrant_settings = await get_DB.warrant_settings()

            while True:
                end = datetime.today()
                if end.second in [0, 1]:  #Restrict time to 59 seconds
                    break                         
                if int((end - start).total_seconds()) < 60:
                    await asyncio.sleep(1)
                else:
                    break
            print('*******************')
            if end.hour == 16 and end.minute == 10:
                break

        asyncio.create_task( self.Grab_Warrant_Historys() )

    async def Street_Hunters_disposed(self): # Disposed
        start = datetime.today()
        current_time = time_control()
        codes = await get_DB.hk_stock_all_with_warrant_list()

        stock_list = []
        for code in codes:
            if code:
                stock_list.append('HK.' + code)
        stock_df = self.Futu_Api.get_market_snapshot(code=stock_list)    
        stock_df = stock_df.set_index('code')

        LEN_STOCK = 0
        LEN_WARRANT = 0
        street_hunters = pd.DataFrame()
        for code in codes:
            # code = codes[1]
            if code:
                stock_dict = stock_df.loc['HK.' +code].to_dict()
                warrant_codes_df = await Get_wrt_mkt_closed_db.wrt_code_converstion_delta(
                                                    code=code, 
                                                    time__range=[start - timedelta(days=1), start], 
                                                    )
                warrant_codes_df = warrant_codes_df[warrant_codes_df['last_price'] > 0.019]
                warrant_codes_df = warrant_codes_df[warrant_codes_df['volume'] > 0]
                warrant_codes_list = warrant_codes_df['code'].tolist()
                warrant_codes_df = warrant_codes_df.set_index('code')

                for wrt_code in warrant_codes_list:
                    wrt_conversion_ratio = warrant_codes_df.loc[wrt_code]['wrt_conversion_ratio']
                    wrt_delta = warrant_codes_df.loc[wrt_code]['wrt_delta']
                    wrt_sensitivity = abs( round( (wrt_delta * stock_dict['price_spread'] / wrt_conversion_ratio) * 1000 , 3) )

                warrant_code_list_to_futu = []
                for warrant_code in warrant_codes_list:
                    warrant_code_list_to_futu.append('HK.' + warrant_code)
                warrant_df = self.Futu_Api.get_market_snapshot(code=warrant_code_list_to_futu)

                warrant_df = warrant_df[['code','ask_vol', 'ask_price', 'bid_price','bid_vol','wrt_conversion_ratio','wrt_delta', 'price_spread','stock_owner','wrt_type','wrt_issuer_code']]
                warrant_df['wrt_sensitivity'] = abs( round( (stock_dict['price_spread'] * warrant_df['wrt_delta']) / (warrant_df['wrt_conversion_ratio'] * warrant_df['price_spread']), 3 ) )
                warrant_df['flat_position'] = round( ((warrant_df['ask_price'] - warrant_df['bid_price']) / warrant_df['price_spread'] )/ warrant_df['wrt_sensitivity'], 2)
                warrant_df = warrant_df.drop(['wrt_conversion_ratio','wrt_delta', 'price_spread','wrt_sensitivity'], axis=1)
                warrant_df = warrant_df.sort_values(by=['flat_position'])
                warrant_df = warrant_df[warrant_df['bid_price'] > 0]
                warrant_df = warrant_df[warrant_df['flat_position'] > 0]
                warrant_df = warrant_df[warrant_df['flat_position'] < 20]

                warrant_df['stock_owner'] = warrant_df['stock_owner'].apply(lambda x: x[3:])
                warrant_df['code'] = warrant_df['code'].apply(lambda x: x[3:])
                warrant_df = warrant_df.set_index('code')

                warrant_df = warrant_df[warrant_df['flat_position'] < 1]
                street_hunters = pd.concat( [street_hunters, warrant_df] )

                LEN_WARRANT+=len(warrant_codes_list)

        LEN_STOCK = len(codes)
        print('Stock Total: ', LEN_STOCK)
        print('Warrant Total', LEN_WARRANT)

        street_hunters = street_hunters.drop(['bid_vol','ask_vol', 'ask_price','bid_price'], axis=1)
        with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
            print(street_hunters)

        # for i in range(0, len(warrant_codes) / 400):
        #     if i ==0:
        #         warrant_df = self.Futu_Api.get_market_snapshot(code=warrant_codes[:400])
        #     elif i>0:
        #         warrant_df = self.Futu_Api.get_market_snapshot(code=warrant_codes[i*400:])
        #     warrant_df = warrant_df.set_index('code')
        #     warrant_df = warrant_df[warrant_df['bid_price'] > 0]
        #     warrant_df = warrant_df[warrant_df['ask_vol'] > warrant_df['bid_vol']]
        #     # print(type(warrant_df['bid_vol'].values))
        #     warrant_df = warrant_df[warrant_df['bid_vol'] > 200000]
        #     with pd.option_context('display.max_rows', None, 'display.max_columns', None): 
        #         print(warrant_df[['bid_price','bid_vol','ask_price','ask_vol']])

        #     break

        # Get raise extreme high stock street inventory
        # Collect yesterday bid ask
        # Calculate how warrant move
        # Collect extreme high stock market snap shot
        # Buy before ( add some buffer )
        # monitor High Volume in bull bear!!! Should be someone who buy warrant and stock simultanlously
        print('Time', datetime.today() - start)

    async def Stock_signals_new(self): # Disposed
        print('Start Stock Signals')
        stock_codes = await get_DB.hk_stock_all_with_warrant_list()
        self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
        warrant_settings = await get_DB.warrant_settings()

        while True:
            # Get Futu Api Every 60s
            stocks_snapshot_df = self.Futu_Api.get_market_snapshot(['HK.' + stock_code for stock_code in stock_codes])
            start = datetime.today()
            exDict_list = []
            Street_Hunter_tasks = []

            if not stocks_snapshot_df.empty:   #To avoid error
                print(stocks_snapshot_df)

                # Get Stocks Signals
                stocks_signals_start = datetime.today()
                for i in range(0, len(stocks_snapshot_df)):
                    exDict = asyncio.create_task( self.Stock_signal(
                                                                    stock_code=stocks_snapshot_df.iloc[i].code[3:], 
                                                                    stock_data=stocks_snapshot_df.iloc[i].to_dict(), 
                                                                    warrant_settings=warrant_settings
                                                                ))
                    if exDict:
                        exDict_list.append(exDict)
                exDict_list = await asyncio.gather(*exDict_list)
                exDict_list = [i for i in exDict_list if i] # Data have none
                Total_signals = len(exDict_list)
                exDict_code_list = [i['Stock Code'] for i in exDict_list]

                # Find Signal With Day High and put in the front
                day_high_code_list = [i['Stock Code'] for i in exDict_list if 'Day High' in i['Signal Type']]
                exDict_code_list = [x for x in exDict_code_list if x not in day_high_code_list]
                random.shuffle(exDict_code_list)
                exDict_code_list = day_high_code_list + exDict_code_list

                # Get Warrant Data
                warrant_signals_start = datetime.today()
                for exDict_code in exDict_code_list[:30]:  # Should be to api
                    Street_Hunter_task = asyncio.create_task( self.Street_Hunter(stock_code=exDict_code) )
                    if Street_Hunter_task:
                        Street_Hunter_tasks.append(Street_Hunter_task)
                        # yield Street_Hunter_task

                selected_warrants = await asyncio.gather(*Street_Hunter_tasks)
                selected_warrants = [i for i in selected_warrants if i] # Data have none

                for exDict in exDict_list:
                    for selected_warrant in selected_warrants:
                        if exDict['Stock Code'] == selected_warrant[0]['stock_owner']:
                            exDict['warrant'] = selected_warrant
                exDict_list = [x for x in exDict_list if 'warrant' in x] #Drop Stock that have no warrant code

                # Send Signal to Websocket
                if exDict_list:
                    await (self.channel_layer.group_send)(
                        'event', 
                        {
                            'type':'receive.json', 
                            'data': {
                                'real_time_stock': exDict_list,
                            }
                        })

            # Set Get Data Timer
            end = datetime.today()
            print('This Process cost:', 
                    round( (end-start).total_seconds(), 2), 'Seconds ', 
                '(Stock Signals Cost:', 
                    round( (warrant_signals_start-stocks_signals_start).total_seconds(), 2),
                '/ ',
                'Warrant Signals Cost:',
                    round( (end-warrant_signals_start).total_seconds(), 2),
                ')',
                )
            print('The Time Now: ', end)
            self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
            self.TIMES_GET_CAPITAL_DISTRIBUTION = 30
            self.TIMES_GET_CAPITAL_FLOW = 30
            print('You Still Have Remain API Subs: ', self.TIMES_REMAIN_API_SUBS )
            print('Total Signals: ', Total_signals)
            print('Total exDict Signals (With Warrants): ', len(exDict_list))

            warrant_settings = await get_DB.warrant_settings()

            while True:
                end = datetime.today()
                if end.second in [0, 1]:  #Restrict time to 59 seconds
                    break                         
                if int((end - start).total_seconds()) < 60:
                    await asyncio.sleep(1)
                else:
                    break
            print('*******************')
            if end.hour == 16 and end.minute == 10:
                break

        asyncio.create_task( self.Grab_Warrant_Historys() )

    async def Stock_signals(self): # Disposed
        print('Start Stock Signal - Volume Extreme')
        stock_codes = await get_DB.hk_stock_all_with_warrant_list()
        self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
        warrant_settings = await get_DB.warrant_settings()

        # warrant_signals_start = datetime.today()
        # exDict_code_list = await get_DB.hk_stock_all_with_warrant_list()
        # accessable_wrt_list = await self.Street_Hunters(exDict_code_list)
        # for accessable_wrt_list in accessable_wrt_list:
        #     snapshot_df = self.Futu_Api.get_market_snapshot(accessable_wrt_list)
        #     stocks_df = snapshot_df[snapshot_df['stock_owner'].isnull()].to_dict(orient='records')  # To find all stock df and turn it to dict
        #     for stock_dict in stocks_df:
        #         stock_spread = stock_dict['price_spread']

        #         warrant_df = snapshot_df[snapshot_df['stock_owner'] == stock_dict['code']]
        #         warrant_df = warrant_df[['code','update_time', 'ask_vol', 'ask_price', 'bid_price','bid_vol','wrt_conversion_ratio','wrt_delta', 'price_spread','stock_owner','wrt_type','wrt_issuer_code']]
        #         warrant_df['wrt_sensitivity'] = abs( round( (stock_spread * warrant_df['wrt_delta']) / (warrant_df['wrt_conversion_ratio'] * warrant_df['price_spread']), 3 ) )
        #         warrant_df['flat_position'] = round( ((warrant_df['ask_price'] - warrant_df['bid_price']) / warrant_df['price_spread'] )/ warrant_df['wrt_sensitivity'], 1)

        #         for i in range(0, len(warrant_df)):
        #             if not warrant_df.iloc[i]['code'] == stock_dict['code']: # Exclude Stock Dict
        #                 await futu_to_db(stock_dict['code'][3:], warrant_df.iloc[i].to_dict(), 'hk_warrant_timescale', stock_dict=stock_dict)
        # print(datetime.today() - warrant_signals_start)

        while True:
            # Get Futu Api Every 60s
            stocks_snapshot_df = self.Futu_Api.get_market_snapshot(['HK.' + stock_code for stock_code in stock_codes])
            start = datetime.today()
            exDict_list = []
            Street_Hunter_tasks = []

            if not stocks_snapshot_df.empty:   #To avoid error
                print(stocks_snapshot_df)

                # Get Stocks Signals
                stocks_signals_start = datetime.today()
                for i in range(0, len(stocks_snapshot_df)):
                    exDict = asyncio.create_task( self.Stock_signal(
                                                                    stock_code=stocks_snapshot_df.iloc[i].code[3:], 
                                                                    stock_data=stocks_snapshot_df.iloc[i].to_dict(), 
                                                                    warrant_settings=warrant_settings
                                                                ))
                    if exDict:
                        exDict_list.append(exDict)
                exDict_list = await asyncio.gather(*exDict_list)
                exDict_list = [i for i in exDict_list if i] # Data have none
                Total_signals = len(exDict_list)
                exDict_code_list = [i['Stock Code'] for i in exDict_list]

                # Find Signal With Day High and put in the front
                day_high_code_list = [i['Stock Code'] for i in exDict_list if 'Day High' in i['Signal Type']]
                exDict_code_list = [x for x in exDict_code_list if x not in day_high_code_list]
                random.shuffle(exDict_code_list)
                exDict_code_list = day_high_code_list + exDict_code_list

                # Get Warrant Data
                warrant_signals_start = datetime.today()
                for exDict_code in exDict_code_list[:30]:  # Should be to api
                    Street_Hunter_task = asyncio.create_task( self.Street_Hunter(stock_code=exDict_code) )
                    if Street_Hunter_task:
                        Street_Hunter_tasks.append(Street_Hunter_task)

                selected_warrants = await asyncio.gather(*Street_Hunter_tasks)
                selected_warrants = [i for i in selected_warrants if i] # Data have none

                for exDict in exDict_list:
                    for selected_warrant in selected_warrants:
                        if exDict['Stock Code'] == selected_warrant[0]['stock_owner']:
                            exDict['warrant'] = selected_warrant
                exDict_list = [x for x in exDict_list if 'warrant' in x] #Drop Stock that have no warrant code

                # Send Signal to Websocket
                if exDict_list:
                    await (self.channel_layer.group_send)(
                        'event', 
                        {
                            'type':'receive.json', 
                            'data': {
                                'real_time_stock': exDict_list,
                            }
                        })

            # Set Get Data Timer
            end = datetime.today()
            print('This Process cost:', 
                    round( (end-start).total_seconds(), 2), 'Seconds ', 
                '(Stock Signals Cost:', 
                    round( (warrant_signals_start-stocks_signals_start).total_seconds(), 2),
                '/ ',
                'Warrant Signals Cost:',
                    round( (end-warrant_signals_start).total_seconds(), 2),
                ')',
                )
            print('The Time Now: ', end)
            self.TIMES_REMAIN_API_SUBS = self.Futu_Api.query_subscription()['remain']
            self.TIMES_GET_CAPITAL_DISTRIBUTION = 30
            self.TIMES_GET_CAPITAL_FLOW = 30
            print('You Still Have Remain API Subs: ', self.TIMES_REMAIN_API_SUBS )
            print('Total Signals: ', Total_signals)
            print('Total exDict Signals (With Warrants): ', len(exDict_list))

            warrant_settings = await get_DB.warrant_settings()

            while True:
                end = datetime.today()
                if end.second in [0, 1]:  #Restrict time to 59 seconds
                    break                         
                if int((end - start).total_seconds()) < 60:
                    await asyncio.sleep(1)
                else:
                    break
            print('*******************')
            if end.hour == 16 and end.minute == 10:
                break

        asyncio.create_task( self.Grab_Warrant_Historys() )

    async def Street_Hunter(self, stock_code, warrant_df=None): # Disposed
        if not warrant_df:
            current_time = time_control()
            stock_qs = await get_DB.hk_stock(code=stock_code)
            warrant_codes_df = await Get_wrt_mkt_closed_db.wrt_code_converstion_delta(
                                                stock_owner=stock_qs, 
                                                time__range=[current_time - timedelta(days=5), current_time], 
                                                )

            try: # When Stock has not match warrant
                warrant_codes_df = warrant_codes_df[warrant_codes_df['last_price'] > 0.019]
                warrant_codes_list = warrant_codes_df['code'].tolist()
            except:
                warrant_codes_list = []
                print('warrant_codes_df not found ' , stock_code)

            warrant_code_list_to_futu = ['HK.' + stock_code]
            for warrant_code in warrant_codes_list:
                warrant_code_list_to_futu.append('HK.' + warrant_code)
            warrant_code_list_to_futu = list(set(warrant_code_list_to_futu))   # To remove duplicate due to timedelta not stable
            warrant_df = self.Futu_Api.get_market_snapshot(code=warrant_code_list_to_futu)

        # Get Stock Price Spread
        try:
            stock_dict = warrant_df[warrant_df['code'] == 'HK.' + stock_code].to_dict(orient='records')[0]
            stock_spread = stock_dict['price_spread']
        except:  # Useless???
            stock_dict = await get_DB.hk_stock(code=stock_code).to_dict()
            stock_spread = stock_dict['price_spread']

        # Calculate wrt_sen and flat_position
        warrant_df = warrant_df[['code','update_time', 'ask_vol', 'ask_price', 'bid_price','bid_vol','wrt_conversion_ratio','wrt_delta', 'price_spread','stock_owner','wrt_type','wrt_issuer_code']]
        warrant_df['wrt_sensitivity'] = abs( round( (stock_spread * warrant_df['wrt_delta']) / (warrant_df['wrt_conversion_ratio'] * warrant_df['price_spread']), 3 ) )
        warrant_df['flat_position'] = round( ((warrant_df['ask_price'] - warrant_df['bid_price']) / warrant_df['price_spread'] )/ warrant_df['wrt_sensitivity'], 1)

        # Save each of warrant_df into database # TODO can use async to be multi task
        for i in range(0, len(warrant_df)):
            if not warrant_df.iloc[i]['code'] == 'HK.' + stock_code: # Exclude Stock Dict
                await futu_to_db(stock_code, warrant_df.iloc[i].to_dict(), ['hk_warrant_timescale'], stock_dict=stock_dict)

        # Actual 
            # Bid - ask = price spread?
            # %
            # k
        # Actual Predict
        # Pure Predict

        warrant_df = warrant_df.drop(['wrt_conversion_ratio','wrt_delta', 'price_spread','wrt_sensitivity'], axis=1)
        warrant_df = warrant_df[warrant_df['bid_price'] > 0]
        warrant_df = warrant_df[warrant_df['flat_position'] > 0]
        warrant_df = warrant_df[warrant_df['flat_position'] < 20]
        warrant_df = warrant_df.sort_values(by=['flat_position'])[:9]

        warrant_df['stock_owner'] = warrant_df['stock_owner'].apply(lambda x: x[3:])
        warrant_df['code'] = warrant_df['code'].apply(lambda x: x[3:])
        warrant_df = warrant_df.set_index('code')
        warrant_df = warrant_df[warrant_df['flat_position'] < self.FLAT_POSITION]
        warrant_df['code'] = warrant_df.index

        if not warrant_df.empty:
            warrant_dict = warrant_df.to_dict(orient='records')
            return warrant_dict

def time_control():
    current_time = datetime.today()
    if current_time.weekday() not in [5,6]:  # Weekdays
        # Lunch Hour
        if current_time.hour == 12:
            current_time = datetime.today().replace(hour=12, minute=0)

        # Non-Trading Hour (Early)
        if current_time.hour < 9: 
            if current_time.weekday() in [0]:  # Monday
                current_time = datetime.today().replace(hour=16, minute=8) - timedelta(days=3)
            else: # Tue-Friday
                current_time = datetime.today().replace(hour=16, minute=8) - timedelta(days=1)

        # Non-Trading Hour (late)
        if (current_time.hour == 16 and current_time.minute > 10) or current_time.hour > 16:
            current_time = datetime.today().replace(hour=16, minute=8)

    else:  # Sat, Sun
        current_time = datetime.today().replace(hour=16, minute=8) - timedelta(days=current_time.weekday() - 4)
    return current_time

class _Time_control():
    # current_time = datetime.time()

    def __init__(self) -> None:
        self.current_time = datetime.today()

    def __get__(self, *args, **kwds):
        return self.time()

    def __call__(self,) -> list:
        pass

    def time(self) -> datetime:
        if self.current_time.weekday() not in [5,6]:  # Weekdays
            # Lunch Hour
            if self.current_time.hour == 12:
                self.current_time = datetime.today().replace(hour=12, minute=0, second=0)

            # Non-Trading Hour (Early)
            elif self.current_time.hour < 9: 
                if self.current_time.weekday() in [0]:  # Monday
                    self.current_time = datetime.today().replace(hour=16, minute=8, second=0) - timedelta(days=3)
                else: # Tue-Friday
                    self.current_time = datetime.today().replace(hour=16, minute=8, second=0) - timedelta(days=1)

            # Non-Trading Hour (late)
            elif (self.current_time.hour == 16 and self.current_time.minute > 10) or self.current_time.hour > 16:
                self.current_time = datetime.today().replace(hour=16, minute=8, second=0)

            else:
                self.current_time = self.current_time

        else:  # Sat, Sun
            self.current_time = datetime.today().replace(hour=16, minute=8, second=0) - timedelta(days=self.current_time.weekday() - 4)
        return self.current_time

    def is_trading_time(self) -> boolean:
        if self.current_time.weekday() not in [5,6]:  # Weekdays
            # Lunch Hour
            if self.current_time.hour == 12:
                return False

            # Non-Trading Hour (Morning)
            if self.current_time.hour < 9 or (self.current_time.hour == 9 and self.current_time.minute < 30): 
                return False

            # Non-Trading Hour (Night)
            if self.current_time.hour >= 16:
                return False

            return True

        else:  # Sat, Sun
            return False

@database_sync_to_async
def pack_to_warrant_recommend(start_date, end_date):
    exDict_list = []
    for i in tqdm( warrant_market_closed.objects.filter(update_timestamp__range=[start_date, end_date]) ):
        exDict = {}
        traded_positions_dataframe = pd.DataFrame.from_dict(i.wrt_transaction)
        if not traded_positions_dataframe.empty:
            out_put = traded_positions(traded_positions_dataframe)
            if out_put:
                if out_put['max_profit_times'] > out_put['max_loss_times']:
                    if out_put['max_profit_times'] - out_put['max_loss_times'] > 2:
                        exDict['Stock Code']=str(i.stock_owner.code)
                        exDict['Warrant Code']=str(i.code)
                        exDict['Warrant Provider']=str(i.wrt_issuer_code)
                        exDict['Warrant Type']=str(i.wrt_type)
                        exDict['Max Profit Times']=out_put['max_profit_times']
                        exDict['Max Profit Positions']=out_put['max_profit_positions']
                        exDict['Max Loss Times']=out_put['max_loss_times']
                        exDict['Max Loss Positions']=out_put['max_loss_positions']
                        exDict['Remained Amount']=out_put['remained_amount']
                        exDict_list.append(exDict)
    warrant_recommend.objects.create(output_dict=exDict_list)

def for_all_methods(decorator):
    def decorate(cls):
        for attr in cls.__dict__:
            if callable(getattr(cls, attr)):
                setattr(cls, attr, decorator(getattr(cls, attr)))
        return cls
    return decorate

#? Async To DB Methods
@for_all_methods(database_sync_to_async)
class get_DB():
    # Funtional
    def warrant_settings(self) -> list:
        return eval(warrant_setting.objects.get()['settings'][0])

    def clean_wrt_code_in_hk_stock(self):
        pass
        # for i in range(10000, 100000):
        #     codes = get_database(db=['hk_stock_all_with_warrant_list'])

    # HK Stock DataBase
    def hk_stock(self, code:str) -> QuerySet:
        return hk_stock.objects.get(code=code)

    def hk_stock_timescale_delete(self, code:str, time__range:list):
        qs = hk_stock_timescale.objects.filter(code=code, time__range=time__range)
        for i in qs:
            qs.delete()

    def hk_stock_all_with_warrant_list(self) -> list:
        return hk_stock.objects.all_with_warrant_list()

    def hk_stock_create_item(self, code:str):
        return hk_stock.objects.create(code=code)

    # HK Stock Timescale
    def hk_stock_timescale(self, code:str, time__range:list) -> dict:
        qs = hk_stock_timescale.timescale.filter(code=code, time__range=time__range).last()
        try:
            return model_to_dict ( qs )
        except:
            return None

    def hk_stock_timescale_history(self, code:str, time__range:list, current_time:timedelta):
        # return hk_stock_timescale.timescale.filter(code=code, time__range=time__range).values('last_price').histogram(field='last_price', min_value=11, max_value=16, num_of_buckets=10)

        # To get MA data with longer period
        qs = hk_stock_timescale.timescale.filter(code=code, time__range=time__range)
        price_volume_list = qs.values('time', 'last_price','volume').to_list()
        try:
            # To get day high / low with today period
            today_qs = qs.filter(code=code, time__range=[current_time - timedelta(hours=9), current_time])
            day_high = today_qs.aggregate(Max('high_price'))['high_price__max']
            day_low = today_qs.exclude(low_price=0).aggregate(Min('low_price'))['low_price__min']
            try:
                hk_stock_dict = model_to_dict ( today_qs.last() )
            except:
                if (current_time.hour == 9 and current_time.minute < 31) or (current_time.hour == 12):
                    hk_stock_dict = None
                else:
                    hk_stock_dict = None
                    print(current_time)
                    print('hk_stock_timescale_history error', len(today_qs))
        except:
            day_high = None
            day_low = None
            hk_stock_dict = None
        return price_volume_list, day_high, day_low, hk_stock_dict

    def hk_stock_timescale_all_history(self, code:str, time__range:list) -> list:
        qs = list( hk_stock_timescale.timescale.filter(code=code, time__range=time__range).values() )
        return qs

    def test(self):
        qs = hk_warrant.objects.filter(code='55892').select_related('code__bid_price')
        print(qs)
        time.sleep(5)
        print(qs)
        # the_list = ['00001','00005','00388']
        # qs = hk_warrant.objects.raw(
        #     f"SELECT * FROM warrant_hk_stock_timescale WHERE code_id IN \
        #         (SELECT * FROM warrant_hk_stock WHERE code IN ('00001'));"
        #     # "Select * From warrant_hk_stock_timescale.INFORMATION_SCHEMA.COLUMNS;"
        # )
        # qs = list( qs )
        # return qs

@for_all_methods(database_sync_to_async)
class Get_hk_wrt_db():
    def all_code_list(self) -> list:
        return hk_warrant.objects.all_list()

    def code_converstion_delta(self, stock_code:str) -> pd.DataFrame:
        qs = hk_warrant.objects.filter(stock_owner__code=stock_code).values('code', 'wrt_type', 'wrt_issuer_code')
        return pd.DataFrame(qs)

    def all_code_converstion_delta(self, stock_codes_list:list) -> pd.DataFrame:
        qs = hk_warrant.objects.filter(stock_owner__code__in=stock_codes_list).values('code', 'wrt_type', 'wrt_issuer_code')
        return pd.DataFrame(qs)

    def delete(self, code:str) -> pd.DataFrame:
        print( hk_warrant.objects.filter(code=code).delete() )

    def update(self, code, wrt_dict):
        qs = hk_warrant.objects.update_or_create(
                                                code=code,
                                                defaults={
                                                    'name'                         : '',
                                                    'stock_owner'                  : hk_stock.objects.get_or_create(code=wrt_dict['stock_owner'])[0], 
                                                    # Status Related
                                                    'wrt_strike_price'             : wrt_dict['wrt_strike_price'],
                                                    'wrt_status'                   : wrt_dict['wrt_status'],
                                                    'wrt_conversion_ratio'         : wrt_dict['wrt_conversion_ratio'],
                                                    'wrt_type'                     : wrt_dict['wrt_type'],
                                                    'wrt_issuer_code'              : wrt_dict['wrt_issuer_code'],
                                                    # Date Related
                                                    'listing_date'                 : wrt_dict['listing_date'],
                                                    'wrt_maturity_date'            : wrt_dict['wrt_maturity_date'],
                                                    'wrt_end_trade'                : wrt_dict['wrt_end_trade'],
                                                }
        )

@for_all_methods(database_sync_to_async)
class Get_hk_wrt_timescale_db():
    def delete(self, code:str, time_range:list):
        hk_warrant_timescale.objects.filter(code=code, time__range=time_range).delete()

    def delete_duplicated(self, code:str, time__range:list):
        code = hk_warrant.objects.get(code=code)
        #? delete bid = 0 and ask = 0
        # while True:
        #     qs = hk_warrant_timescale.objects.filter(code=code, time__range=time__range).last()
        #     if qs:
        #         if qs.bid_price == 0 and qs.ask_price == 0:
        #             qs.delete()
        #         else:
        #             break
        #     else:
        #         break

        for row in hk_warrant_timescale.objects.filter(code=code, time__range=time__range):
            #? delete bid == aks
            # if row.stock_bid_price == row.stock_ask_price: # Some data wrong
            #     row.delete()

            data = list(hk_warrant_timescale.objects.filter(code=code, time__range=[row.time - timedelta(seconds=30), row.time + timedelta(seconds=30)]))
            if len(data) > 1:
                #? to delete duplicate not tested
                # for i in range(0, len(data) - 1):
                #     if data[i].bid_price == data[i + 1].bid_price and data[i].ask_price == data[i + 1].ask_price and data[i].stock_bid_price == data[i + 1].stock_bid_price and data[i].stock_ask_price == data[i + 1].stock_ask_price:
                #         print(data[i].code)
                #         break

                # if bid price , ask price != 0 and stock bid ask != others
                for i in data:
                    if i != data[-1]:
                        i.delete()

    def history(self, code:str, time__range:list, last:boolean=False) -> pd.DataFrame:
        if last:
            qs = hk_warrant_timescale.timescale.filter(code=code, time__range=time__range).last()
            return model_to_dict(qs)
        else:
            qs = hk_warrant_timescale.timescale.filter(code=code, time__range=time__range)
            warrant_df = pd.DataFrame(qs.values().to_list())
            return warrant_df

    def history_by_stock_owner(self, stock_code:str, time__range:list, last:boolean=False) -> pd.DataFrame:
        qs = hk_warrant_timescale.timescale.filter(stock_owner__code=stock_code, time__range=time__range)
        warrant_df = pd.DataFrame(qs.values().to_list())
        try:
            warrant_df['time'] = warrant_df['time'].dt.tz_convert('Asia/Hong_Kong')
            return warrant_df
        except:
            print('Time is not exist', stock_code)
            return pd.DataFrame()

    def all_history_by_stock_owner(self, stock_codes_list:list, time__range:list, last:boolean=False) -> pd.DataFrame:
        qs = hk_warrant_timescale.timescale.filter(stock_owner__code__in=stock_codes_list, time__range=time__range)
        warrant_df = pd.DataFrame(qs.values().to_list())
        try:
            warrant_df['time'] = warrant_df['time'].dt.tz_convert('Asia/Hong_Kong')
            return warrant_df
        except:
            print('HK Wrt Timescale DB: History Time is not exist', stock_codes_list)
            return pd.DataFrame()

@for_all_methods(database_sync_to_async)
class Get_hk_stock_db():
    def hk_stock(self, code:str) -> QuerySet:
        return hk_stock.objects.get(code=code)

    def hk_stock_timescale_delete(self, code:str, time__range:list):
        qs = hk_stock_timescale.objects.filter(code=code, time__range=time__range)
        for i in qs:
            qs.delete()

    def hk_stock_all_with_warrant_list(self) -> list:
        return hk_stock.objects.all_with_warrant_list()

    def hk_stock_create_item(self, code:str):
        return hk_stock.objects.create(code=code)

@for_all_methods(database_sync_to_async)
class Get_hk_stock_timescale_db():
    def hk_stock_timescale(self, code:str, time__range:list) -> dict:
        qs = hk_stock_timescale.timescale.filter(code=code, time__range=time__range).last()
        try:
            return model_to_dict ( qs )
        except:
            return None

    def hk_stock_timescale_history(self, code:str, time__range:list, current_time:timedelta):
        # return hk_stock_timescale.timescale.filter(code=code, time__range=time__range).values('last_price').histogram(field='last_price', min_value=11, max_value=16, num_of_buckets=10)

        # To get MA data with longer period
        qs = hk_stock_timescale.timescale.filter(code=code, time__range=time__range)
        price_volume_list = qs.values('time', 'last_price','volume').to_list()
        try:
            # To get day high / low with today period
            today_qs = qs.filter(code=code, time__range=[current_time - timedelta(hours=9), current_time])
            day_high = today_qs.aggregate(Max('high_price'))['high_price__max']
            day_low = today_qs.exclude(low_price=0).aggregate(Min('low_price'))['low_price__min']
            try:
                hk_stock_dict = model_to_dict ( today_qs.last() )
            except:
                if (current_time.hour == 9 and current_time.minute < 31) or (current_time.hour == 12):
                    hk_stock_dict = None
                else:
                    hk_stock_dict = None
                    print(current_time)
                    print('hk_stock_timescale_history error', len(today_qs))
        except:
            day_high = None
            day_low = None
            hk_stock_dict = None
        return price_volume_list, day_high, day_low, hk_stock_dict

    def hk_stock_timescale_all_history(self, code:str, time__range:list) -> list:
        qs = list( hk_stock_timescale.timescale.filter(code=code, time__range=time__range).values() )
        return qs

    def all_history(self, stock_codes_list:list, time__range:list) -> pd.DataFrame:
        qs = hk_stock_timescale.timescale.filter(code__code__in=stock_codes_list, time__range=time__range)
        warrant_df = pd.DataFrame(qs.values('time','code', 'last_price','open_price', 'high_price','low_price', 'volume' ).to_list())
        try:
            warrant_df['time'] = warrant_df['time'].dt.tz_convert('Asia/Hong_Kong')
            return warrant_df
        except:
            print('HK Stock Timescale DB: History Time is not exist', stock_codes_list)
            return pd.DataFrame()

@for_all_methods(database_sync_to_async)
class Get_wrt_mkt_closed_db():
    def latest(self, code:str, time_range:list) -> dict:
        wrt_qs = warrant_market_closed.objects.filter(code=code, update_timestamp__range=time_range).last()
        try:
            return model_to_dict(wrt_qs)
        except:
            return None

    def wrt_code_converstion_delta(self, time__range:list, code:str=None, stock_owner:QuerySet=None):
        if code:
            stock_owner = self.hk_stock(code)
        warrant_codes_df = warrant_market_closed.objects.filter(stock_owner=stock_owner, update_timestamp__range=time__range).values('code', 'wrt_conversion_ratio', 'wrt_delta','last_price','volume','price_spread','wrt_type','wrt_issuer_code')
        return pd.DataFrame(warrant_codes_df)

    def wrt_mkt_cl(self, code:str, time__range:list) -> boolean:
        if warrant_market_closed.objects.filter(code=code, update_timestamp=time__range).exists():
            return True

    def get_wrt_vol(self, code:str, time__range:list) -> boolean:
        if warrant_market_closed.objects.get_volume(code=code, time__range=time__range) != 0:
            return True

    def get_wrt_no(self, code:str, time__range:list) -> pd.DataFrame:
        warrant_codes_df = list( warrant_market_closed.objects.filter(stock_owner=code, update_timestamp__range=time__range).values('code') )
        return warrant_codes_df

    def wrt_recommend(self) -> dict:
        return warrant_recommend.objects.get_latest()
