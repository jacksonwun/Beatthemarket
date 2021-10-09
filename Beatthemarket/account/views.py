from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from django.db.models import Max, Min
from django.shortcuts import render
from futu.common.utils import is_str

from warrant.views import *
from warrant.models import *

import pandas as pd
from datetime import date, datetime, timedelta
import csv, time, json

from warrant.consumers import WarrantConsumer

def Dash_board(request):
    get_object = hk_stock.objects.get(code='00700')
    df = pd.DataFrame(hk_stock_timescale.objects.filter(code=get_object).order_by('-time')[:11].values())
    df['diff_volume'] = abs(df['volume'].diff())
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print(df)
    x = round(df.iloc[1]['diff_volume'] / df.iloc[2:]['diff_volume'].mean())
    print(x)

    return render(request, 'dashboard.html')

def Real_Time_Info(request):
    Futu_Api = futu_Api()

    codes = get_codes_from_warrant_list()
    channel_layer = get_channel_layer()

    while True:
        df = Futu_Api.get_stock_quote(['HK.' + s for s in codes])
        exDict_list = []
        if not (df.empty):
            for i in range(0, len(df)):

                try:
                    futu_to_db(df.iloc[i].code[3:], df.iloc[i], 'hk_stock_timescale')
                except:
                    pass

                diff_voluem_muliplier, price_change = cal_volume_extreme(code=df.iloc[i].code[3:], num_data=11)
                if diff_voluem_muliplier:
                    if diff_voluem_muliplier > 10:   #multiplier 10x times
                        try:
                            d = datetime.today() - timedelta(hours=12)
                            today_qs = hk_stock_timescale.objects.filter(code= hk_stock.objects.get(code=df.iloc[i].code[3:]),time__range=[d, datetime.today()])
                            day_high = today_qs.aggregate(Max('high_price'))['high_price__max']
                            day_low = today_qs.aggregate(Min('last_price'))['last_price__min']
                        except:
                            day_high = None
                            day_low = None

                        print('Extreme Volume Monitor Alert: ')
                        print('Code: ' , df.iloc[i].code[3:])
                        print('Price Change: ', price_change)
                        print('High Price: ', day_high)
                        print('Low Price: ', day_low)

                        exDict = {}
                        exDict['Signal Type'] = 'Extreme Volume'
                        exDict['Stock Code'] = df.iloc[i].code[3:]
                        exDict['Price Change'] = price_change
                        exDict['Day High'] = day_high
                        exDict['Day Low'] = day_low
                        exDict['Current Price'] = df.iloc[i].last_price
                        exDict_list.append(exDict)
            async_to_sync(channel_layer.group_send)('event', {'type':'receive.json', 'data': {'real_time_stock':exDict_list}})
        time.sleep(60)
        print('*******************')

    Futu_Api.close()
    return render(request, 'realTimeInfo.html')

def Warrant(request):
    #大額成交
    print(datetime.today())
    Futu_Api = futu_Api()

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

    start_date= datetime.today().replace(hour=16, minute=0, second=0, microsecond=0)
    end_date= datetime.today().replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(hours=12)
    for code in codes:

        object_list = Futu_Api.get_warrant('HK.' + code, req_num=200, type_list=['CALL','PUT','BULL','BEAR'])
        for i in object_list['stock']:
            # print(i)

            if not warrant_market_closed.objects.filter(code=i[3:], update_timestamp__range=[start_date, end_date]):
                # print('check')
                object_list = Futu_Api.get_market_snapshot(i)
                futu_to_db(code, object_list.to_dict(), 'warrant_market_closed')

            if not warrant_market_closed.objects.filter(code=i[3:], update_timestamp__range=[start_date, end_date], volume=0):
                # print('checking')
                Futu_Api.subscribe(i, 'TICKER')
                object_list = Futu_Api.get_rt_ticker(i)
                futu_to_db(i[3:], object_list.to_dict(), 'warrant_transaction')
                Futu_Api.unsubscribe(i)

    print(datetime.today())
    Futu_Api.close()

    return render(request)

def Crypto(request):
    print('Warrant Calculate')
    start_date= datetime.today().replace(hour=16, minute=0, second=0, microsecond=0) - timedelta(hours=24)
    end_date= datetime.today().replace(hour=16, minute=0, second=0, microsecond=0) + timedelta(hours=12)
    exDict_list = []
    file = open('file2.txt', 'w')
    file.truncate(0)
    for i in warrant_market_closed.objects.filter(update_timestamp__range=[start_date, end_date]):
        print(i.code)
        exDict = {}
        traded_positions_dataframe = pd.DataFrame.from_dict(i.wrt_transaction)
        if not traded_positions_dataframe.empty:
            out_put = traded_positions(traded_positions_dataframe)
            if out_put:
                if out_put['max_profit_times'] > out_put['max_loss_times']:
                    # if out_put['max_loss_times'] == 0 and out_put['max_profit_times'] > 1:
                    #     print('*****************')
                    if out_put['max_profit_times'] - out_put['max_loss_times'] > 2:
                        print('*****************')
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
    file.write(str(json.dumps(exDict_list)) + '\n')
    return render(request, 'crypto.html')

def Sentiment(request):
    print('senti')
    
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_add)('test', 'test')
    print(async_to_sync(channel_layer.group_send)('event', {'type':'receive.json', 'data': {'message':'stockSignalStart'}}))

    return render(request, 'sentiment.html')

def Algo_Trade(request):
    return render(request, 'algoTrade.html')

def Settings(request):
    return render(request, 'settings.html')

