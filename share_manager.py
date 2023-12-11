import pandas as pd
import numpy as np
import robin_stocks as stonks
import math
import time
import statistics
import tradingview_ta as sa


def filter_stocks(data_frame, share_data, num_stocks, volatility_min=0.6, auto_volatility=7, volume=1000000, buying_power=1000, owned_stocks = [None]):   # Goes through csv and picks suitable stocks based on magnitude of price fluctuations (higher is more desirable)
    share_volatile = []
    share_index = []
    share_data_copy = share_data
    exchange = 'NASDAQ'
    screener = 'america'
    interval = sa.Interval.INTERVAL_30_MINUTES
    print('Filtering stocks...')
    # Filters out list of stocks by a threshold volatility (scale of price changes) and trade volume
    for index, raw_share_info in data_frame.iterrows():
        if raw_share_info['Volume'] is not None:
            if float(raw_share_info['Volume']) >= volume:
                share_volatile.append(raw_share_info['Volatility'])
    # Filters out the top num_stocks highest volatile stocks
    share_volatile = sorted(share_volatile)
    share_volatile.reverse()
    # Uses Trading TA API to verify that MACD values exist for that ticker as well as verifying that stock exists in Robinhood
    if owned_stocks[0] is not None:
        if owned_stocks[0] != '':   # Appends already owned stocks so that they're not dropped on a day to day basis
            for x in owned_stocks:
                share_data_copy.append(x)
    for x in share_volatile:
        if len(share_data_copy) < num_stocks:
            for index, i in data_frame['Volatility'].items():
                if type(i) == float:
                    if x == i:
                        stock = data_frame['Symbol'][index]
                        try:
                            if float(stonks.robinhood.stocks.get_latest_price(stock)[0]) > 0.0 and float(stonks.robinhood.stocks.get_latest_price(stock)[0]) <= buying_power:
            
                                    handler = sa.TA_Handler(symbol=stock, screener=screener, exchange=exchange, interval=interval)
                                    stock_data = handler.get_analysis()
                                    share_data_copy.append(stock)
                        except Exception:
                            continue
        else:
            break
    
    print('\nFiltered out stocks:\n')
    for x in share_data_copy:
        print(x)
    
            
    return share_data_copy

def format_csv(data_frame,stock_path,re_write=False):
    if re_write:
        for index, new_share_info in data_frame.iterrows():
            print('Calculating volatility for:', new_share_info['Symbol'])
            prices = stonks.robinhood.stocks.get_stock_historicals(new_share_info['Symbol'], interval='hour', span='day')[:8]
            print(prices)
            if prices:
                if prices is not None:
                    prices = [float(x) for x in prices]
                    volatility = np.log(prices).std()*252**.5  # 252 trading days in a year
                    data_frame.loc[index, 'volatility'] = volatility

        for index, new_share_info in data_frame.iterrows():
            print('Adding volume for:', new_share_info['Symbol'])
            volume = stonks.robinhood.stocks.get_fundamentals(new_share_info['Symbol'], info='average_volume_2_weeks')
            if volume:
                if volume[0] is not None:
                    data_frame.loc[index, 'Volume'] = float(volume[0])
    
        data_frame.to_csv('C:\\Users\\Quamez\\source\\repos\\RL Projects\\AutoTrader\\nasdaqlist_formatted.csv',index=False)
    
    new_data = pd.read_csv('C:\\Users\\Quamez\\source\\repos\\RL Projects\\AutoTrader\\nasdaqlist_formatted.csv',index_col=False)
    dropped = False
    for index, new_share_info in new_data.iterrows():
        test = stonks.robinhood.stocks.get_stock_historicals(new_share_info['Symbol'], interval='10minute', span='day', info='close_price', bounds='extended')
        if type(test[0]) != str:
            print('Volatility not found:',test)
            print(new_data.loc[index,'Symbol'], 'being deleted at', index)
            new_data.drop(index,inplace=True)
            new_data.to_csv('C:\\Users\\Quamez\\source\\repos\\RL Projects\\AutoTrader\\nasdaqlist_formatted.csv',index=False)
            dropped = True
        test = stonks.robinhood.stocks.get_fundamentals(new_share_info['Symbol'], info='average_volume')
        if type(test[0]) != str and not dropped:
            print('Volume not found:',test)
            print(new_data.loc[index,'Symbol'], 'being deleted at', index)
            new_data.drop(index,inplace=True)
            new_data.to_csv('C:\\Users\\Quamez\\source\\repos\\RL Projects\\AutoTrader\\nasdaqlist_formatted.csv',index=False)
        dropped = False
        #print(new_share_info['Symbol'])

def calc_rsi(period, close_prices):
    change = close_prices
    change_up = change.copy()
    change_down = change.copy()
  
    change_up[change_up<0] = 0
    change_down[change_down>0] = 0

    # Verify that we did not make any mistakes
    change.equals(change_up+change_down)

    # Calculate the rolling average of average up and average down
    avg_up = change_up.rolling(period).mean()
    avg_down = change_down.rolling(period).mean().abs()
    rsi = 100 * avg_up / (avg_up + avg_down)
    rsi.head(20)

                

def write_csv(data_frame, time_start, stock_path):
    # Test volatility calculations using lists instead of dataframes since it's MUCH faster
    stuff = data_frame['Symbol'].values.tolist()
    test_volatility = np.full(1,-1,dtype=float)
    # For converting price groupings into stock tickers
    num_prices = 1 + (int(time_start) - 900 -(40 * (int(time_start[0:2]) - 9))) / 10
    num_prices = int(num_prices)
    for i in range(len(stuff)):
        stock_data = stonks.robinhood.stocks.get_stock_historicals(stuff[i], interval='10minute', span='day', bounds='extended')
        if stock_data[0] is not None:
            time_data = [x.get('begins_at') for x in stock_data]
            price_data = [float(x.get('close_price')) for x in stock_data]
            
            price_indexes = []
            for j in range(len(time_data)):
                time_index = time_data[j].find('T') # Separates time from the rest of the date
                # Gets the hour and minute of the time data being looked at
                hour = time_data[j][time_index+1:time_index+3]
                minute = time_data[j][time_index+4:time_index+6]
                if int(hour + minute) <= int(time_start) and int(hour + minute) >= 900: # Appends all time data up to the desired time
                    price_indexes.append(j)
            for j in range(len(price_indexes)):
                # Uses the nth number of closing prices for each stock and calculates volatility where 12 is the number of close prices at 1100 
                if test_volatility[0] != -1:
                    test_volatility = np.append(test_volatility,price_data[price_indexes[j]])
                else:
                    test_volatility[0] = price_data[price_indexes[j]]

                if (j + 1) % num_prices == 0:
                    test_volatility = np.log(test_volatility).std()*252**.5
                    print('Volatility for', stuff[i] + ':',test_volatility)  # 1 less than the modulus number above
                    data_frame.loc[(i), 'Volatility'] = test_volatility
                    
                    test_volatility = np.full(1,-1,dtype=float)
            
            

            

            volume = stonks.robinhood.stocks.get_fundamentals(stuff[i], info='average_volume_2_weeks')
            print('Volume for', stuff[i] + ':',volume[0])
            data_frame.loc[i, 'Volume'] = volume[0]
            data_frame.to_csv(stock_path, index=False)
        else:
            print('Skipping', stuff[i])
