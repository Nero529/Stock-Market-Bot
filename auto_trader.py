'''
Created by: Quamez Anderson
Date Created: 08 February 2021
'''

import robin_stocks as stonks
import time
import os
import pandas as pd
import numpy as np
import math
import share_manager as stonk_calc

def check_market_open():
    '''
    Stock market is open from 0800 to 1700
    '''

    current_hour = time.strftime("%H")
    current_min = time.strftime("%M")
    current_day = time.strftime("%A")
    #print(current_hour, current_min, current_day)
    if current_day != 'Saturday' and current_day != 'Sunday':
        if (int(current_hour) == 8 or (int(current_hour) > 8)) and not int(current_hour) >= 17:
            return True
        else:
            return False
    else:
        return False
def is_time_interval(minute = -1, hour = -1, second = -1):
    current_hour = time.strftime("%H")
    current_min = time.strftime("%M")
    current_sec = time.strftime("%S")
    if minute != -1:
        minute_check = int(current_min) % minute == 0
    else:
        minute_check = True

    if hour != -1:
         hour_check = int(current_hour) % hour == 0
    else:
        hour_check = True

    if second != -1:
        if minute == -1:
            second_check = int(current_sec) % second == 0
        else:
            second_check = int(current_sec) == 0
            
    else:
        second_check = True
    
    if minute_check and second_check and hour_check:
        time.sleep(1)
        return True
    else:
        time.sleep(1)
        return False

top_of_hour_share_price = 0
buying_power = 1000  # $ Amount in user's account
prev_buying_power = buying_power
non_adjustable_min_cash_limit = 400.
share_data = []
share_index = []
username = input('Please enter your username:')
password = input('Please enter your password:')


try:
    login = stonks.login(username, password, store_session=True)

except:
    print('Invalid login, terminating session')
    raise SystemExit
if login:
    if check_market_open():
        print('Login successful. Accessing user information')


if check_market_open() == False:
    print('Stock market is currently closed\n')

else:
    print('Stock market is currently open\n')

all_share_data = pd.read_csv('new_stuff.csv',index_col=False)

share_data, share_index = stonk_calc.filter_stocks(all_share_data, share_data, share_index)

print()
shares = np.zeros(len(share_data))
bought_price = np.zeros(len(share_data))
macd_sma = [] * len(share_data)
stochastic_sma = np.zeros((len(share_data), 3))

past_macd_signal = np.full(len(share_data), 'None')
past_stochastic_signal = np.full(len(share_data), 'None')
while True:
    if is_time_interval(second=5):
        print('Checking for potential trades...')
        for index_num, stock in enumerate(share_data):
            past_close_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='close_price')
            past_low_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='low_price')
            past_high_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='high_price')
            current_price = float(stonks.get_latest_price(stock)[0])
            share_handler = buying_power / current_price * 0.1 # Amount of shares purchased in one interaction
            if share_handler < 1:
                share_handler = 1
            
            ema_twelve = stonk_calc.get_ema(all_share_data[share_index][index_num], current_price, period=12, past_close_prices=past_close_prices)
            ema_two_six = stonk_calc.get_ema(all_share_data, current_price, period=26, past_close_prices=past_close_prices)
            if pd.isnull(all_share_data.iloc[share_index[index_num]]['MACD']):
                macd_signal = stonk_calc.get_macd(all_share_data, ema_twelve, ema_two_six, period=9, sma_list=macd_sma[index_num])
            else:
                macd_signal = stonk_calc.get_macd(all_share_data, ema_twelve, ema_two_six, period=9)
            
            stochastic_signal, stochastic_sma[index_num] = stonk_calc.get_stochastic(all_share_data, current_price, past_low_prices, past_high_prices, period=3, stochastic_list=stochastic_sma[index_num])

            if shares[index_num] > 0:
                print('Stock:', stock)
                print('Bought Price:', bought_price[index_num])
                print('MACD signal:', macd_signal)
                print('Stochastic signal:', stochastic_signal, '\n')
            #print(index_num)
            #print('Current stock:', stock)
            #print('MACD signal:', macd_signal)
            #print('Stochastic signal:', stochastic_signal, '\n')
            
            if macd_signal == 'SELL' and stochastic_signal == 'SELL' and shares[index_num] != 0 and float(current_price) > bought_price[index_num]:
                print('Selling stock for:', stock)
                buying_power += shares[index_num] * current_price
                shares[index_num] = 0
                print('Previous Buying Power:', prev_buying_power)
                print('Shares profit:', current_price - bought_price[index_num])
                print('Current Buying Power:', buying_power, '\n')
                prev_buying_power = buying_power
                    

            if macd_signal == 'BUY' and past_stochastic_signal[index_num] == 'BUY' and shares[index_num] == 0 and buying_power - (int(share_handler) * current_price) >= non_adjustable_min_cash_limit:
                print('Buying stock for:', stock)
                shares[index_num] += int(share_handler)
                buying_power -= int(share_handler) * current_price
                bought_price[index_num] = current_price
                print('Number of shares:', shares[index_num])
                print('Share price:', bought_price[index_num])
                print('Previous Buying Power:', prev_buying_power)
                print('Current Buying Power:', buying_power, '\n')
                prev_buying_power = buying_power
                   
            #past_macd_signal[index_num] = macd_signal
            past_stochastic_signal[index_num] = stochastic_signal
        all_share_data.to_csv('new_stuff.csv',index=False)
        #print()
        
#my_account = stonks.profiles.load_account_profile()
#buying_power = my_account['buying_power']

while check_market_open():
    if is_time_interval(second=5):
        print('Checking for potential trades...')
        for index_num, stock in enumerate(share_data):
            past_close_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='close_price')
            past_low_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='low_price')
            past_high_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='high_price')
            current_price = float(stonks.get_latest_price(stock)[0])
            share_handler = buying_power / current_price * 0.1 # Amount of shares purchased in one interaction
            if share_handler < 1:
                share_handler = 1
            #ema_twelve = get_ema(current_price, period=12,past_close_prices=past_close_prices)
            ema_twelve = get_ema(current_price, period=12, past_close_prices=past_close_prices)
            ema_two_six = get_ema(current_price, period=26, past_close_prices=past_close_prices)
            if pd.isnull(all_share_data.iloc[share_index[index_num]]['MACD']):
                macd_signal = get_macd(ema_twelve, ema_two_six, period=9, sma_list=macd_sma[index_num])
            else:
                macd_signal = get_macd(ema_twelve, ema_two_six, period=9)
            #if pd.isnull(all_share_data.iloc[share_index[index_num]]['Stochastic']):
            stochastic_signal, stochastic_sma[index_num] = get_stochastic(current_price, past_low_prices, past_high_prices, period=3, stochastic_list=stochastic_sma[index_num])
            print('Stochastic sma:', stochastic_sma)
            if shares[index_num] > 0:
                print('Stock:', stock)
                print('Bought Price:', bought_price[index_num])
                print('MACD signal:', macd_signal)
                print('Stochastic signal:', stochastic_signal, '\n')
            print(index_num)
            #print('Current stock:', stock)
            #print('MACD signal:', macd_signal)
            #print('Stochastic signal:', stochastic_signal, '\n')
            
            if macd_signal == 'SELL' and stochastic_signal == 'SELL' and shares[index_num] != 0 and float(current_price) > bought_price[index_num]:
                print('Selling stock for:', stock)
                buying_power += shares[index_num] * current_price
                shares[index_num] = 0
                print('Previous Buying Power:', prev_buying_power)
                print('Shares profit:', current_price - bought_price[index_num])
                print('Current Buying Power:', buying_power, '\n')
                prev_buying_power = buying_power
                    

            if macd_signal == 'BUY' and past_stochastic_signal[index_num] == 'BUY' and shares[index_num] == 0 and buying_power - (int(share_handler) * current_price) >= non_adjustable_min_cash_limit:
                print('Buying stock for:', stock)
                shares[index_num] += int(share_handler)
                buying_power -= int(share_handler) * current_price
                bought_price[index_num] = current_price
                print('Number of shares:', shares[index_num])
                print('Share price:', bought_price[index_num])
                print('Previous Buying Power:', prev_buying_power)
                print('Current Buying Power:', buying_power, '\n')
                prev_buying_power = buying_power
                   
            #past_macd_signal[index_num] = macd_signal
            past_stochastic_signal[index_num] = stochastic_signal
        all_share_data.to_csv('new_stuff.csv',index=False)
        #print()
        
    #my_account = stonks.profiles.load_account_profile()
    #buying_power = my_account['buying_power']
       
