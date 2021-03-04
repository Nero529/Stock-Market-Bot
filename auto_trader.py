'''
Created by: Quamez Anderson
Date Created: 08 February 2021
'''

import robin_stocks as stonks
import time
import pyotp
import qrcode
from PIL import Image
import os
import pandas as pd
import numpy as np
import math

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

def get_ema(current_price, period, past_close_prices):
    
    if not pd.isnull(all_share_data.iloc[share_index[index_num]]['EMA{}'.format(period)]):
        past_ema = all_share_data.iloc[share_index[index_num]]['EMA{}'.format(period)]
        new_ema = current_price * (2 / (period + 1)) + past_ema * (1- (2 / (period + 1)))
    else:
        mov_avg = 0
        for value in past_close_prices[:period]:
            mov_avg += float(value)
        new_ema = mov_avg / period

    all_share_data.loc[share_index[index_num], 'EMA{}'.format(period)] = new_ema
    return new_ema

def get_macd(ema_one, ema_two, period, sma_list=[]):
    
    macd = ema_one - ema_two
    if not pd.isnull(all_share_data.iloc[share_index[index_num]]['MACD']):
        prev_macd = all_share_data.iloc[share_index[index_num]]['MACD']
        macd_signal = macd * (2 / (period + 1)) + prev_macd * (1 - (2 / (period + 1)))
        macd_histo = macd - macd_signal
        #print('MACD Histo:', macd_histo)
        if macd_histo > 0:
            signal = 'BUY'
        elif macd_histo < 0:
            signal = 'SELL'
            
        return signal
    else:
        sma_list.append(macd)
        sma = 0
        for value in sma_list:
            sma += value
        sma /= period
        if len(sma_list) == period:
            all_share_data.loc[share_index[index_num], 'MACD'] = sma
    




def get_stochastic(current_price, low_prices, high_prices, period, stochastic_list=[]):
    # %K = (recent closing price - lowest price in period) / (highest price in period - lowest)
    # %D = 3 period SMA of %K
    for index, price in enumerate(low_prices[:period]):
        if index == 0:
            lowest_price = float(price)
        else:
            if float(price) < lowest_price:
                lowest_price = float(price)

    for index, price in enumerate(high_prices[:period]):
        if index == 0:
            highest_price = float(price)
        else:
            if float(price) > highest_price:
                highest_price = float(price)

    percent_k = (current_price - lowest_price) / (highest_price - lowest_price) * 100
    stochastic_list.append(percent_k)
    sma = 0
    for value in stochastic_list:
        sma += value
    sma /= period

    percent_k_sma[index_num].append(percent_k)
    if len(percent_k_sma[index_num]) > 3:
        percent_k_sma[index_num].pop(0)
    percent_d = 0
    for x in percent_k_sma[index_num]:
        percent_d += x
    percent_d /= 3
    print('%K:', percent_k)
    print('%D:', percent_d)

    if len(stochastic_list) == period and pd.isnull(all_share_data.iloc[share_index[index_num]]['Stochastic']):
        all_share_data.loc[share_index[index_num], 'Stochastic'] = sma

    elif not pd.isnull(all_share_data.iloc[share_index[index_num]]['Stochastic']):
       
        if percent_k >= 80:
            signal = 'SELL'
        elif percent_k - percent_d > 0 and percent_k <= 20:
            signal = 'BUY'
        else:
            signal = 'HOLD'

        return signal
        


top_of_hour_share_price = 0
buying_power = 1000  # $ Amount in user's account
prev_buying_power = buying_power
non_adjustable_min_cash_limit = 400.
macd_sma = [[]]
stochastic_sma = [[]]
percent_k_sma = [[]]
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

# Gets volatility of a stock
#for index, new_share_info in all_share_data.iterrows():
#    print(new_share_info['Symbol'])
#    calculated_returns = np.zeros(21)
#    deviations = np.zeros(21)
#    closing_prices = stonks.get_stock_historicals(new_share_info['Symbol'], interval='day', span='3month', info='close_price')
#    #print(closing_prices)
#    reversed_prices = closing_prices[::-1]
#    #print(reversed_prices)

#    for num_index, x in enumerate(closing_prices[:21]):
#        if num_index != 0:
#            calculated_returns[num_index] = np.log(float(x) / prev_x)
#        else:
#            calculated_returns[num_index] = float(x)
#        prev_x = float(x)
#        if calculated_returns[num_index] == 0:
#            break
#        #print(calculated_returns[num_index])
#    if len(calculated_returns) == 21:
#        mean = 0
#        for x in calculated_returns:
#            mean += float(x)
#        mean /= len(calculated_returns)
#        for num_index, x in enumerate(calculated_returns):
#            deviations[num_index] = x - mean
#        variance = 0
#        for x in deviations:
#            variance += x ** 2
#        variance /= len(deviations) - 1
#        volatility = math.sqrt(variance)
#        print(volatility)
#        all_share_data.loc[index, 'Volatility'] = volatility

#print('Hello')
#for index, new_share_info in all_share_data.iterrows():
#    print(new_share_info['Symbol'])
#    closing_prices = stonks.get_fundamentals(new_share_info['Symbol'], info='average_volume')
#    all_share_data.loc[index, 'Volume'] = volume

#all_share_data.to_csv('stuff.csv',index=False)
for index, raw_share_info in all_share_data.iterrows():
    #print(raw_share_info['Volume'])
    if float(raw_share_info['Volatility']) > 3 and float(raw_share_info['Volume']) > 5000000:
        share_data.append(raw_share_info['Symbol'])
        share_index.append(index)
        print(raw_share_info['Symbol'])

print()
shares = np.zeros(len(share_data))
bought_price = np.zeros(len(share_data))
past_macd_signal = np.full(len(share_data), 'None')
past_stochastic_signal = np.full(len(share_data), 'None')
while True:
    if is_time_interval(second=30):
        print('Checking for potential trades...')
        for index_num, stock in enumerate(share_data):
            stochastic_sma.append([])
            macd_sma.append([])
            stochastic_sma.append([])
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
            if pd.isnull(all_share_data.iloc[share_index[index_num]]['Stochastic']):
                stochastic_signal = get_stochastic(current_price, past_low_prices, past_high_prices, period=14, stochastic_list=stochastic_sma[index_num])
            else:
                stochastic_signal = get_stochastic(current_price, past_low_prices, past_high_prices, period=14)

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

while check_market_open():
        if is_time_interval(second=30):
            print('Checking for potential trades...')
            for index_num, stock in enumerate(share_data):
                stochastic_sma.append([])
                macd_sma.append([])
                stochastic_sma.append([])
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
                if pd.isnull(all_share_data.iloc[share_index[index_num]]['Stochastic']):
                    stochastic_signal = get_stochastic(current_price, past_low_prices, past_high_prices, period=14, stochastic_list=stochastic_sma[index_num])
                else:
                    stochastic_signal = get_stochastic(current_price, past_low_prices, past_high_prices, period=14)

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
       
