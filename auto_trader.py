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

def get_ema(current_price, period, past_ema=0, past_close_prices):
    
    if past_ema != 0:
        new_ema = current_price * (2 / (period + 1)) + past_ema * (1- (2 / (period + 1)))
    else:
        for index, mov_avg in enumerate(past_close_prices[:period]):
            if index == 0:
                mov_avg = 0
            mov_avg += x
        new_ema = mov_avg / period

    return new_ema

def get_macd(period_one, period_two):





def get_stochastic(current_value, period, past_stochastic):
    # %K = (recent closing price - lowest price in period) / (highest price in period - lowest)
    pass

buying_thresh = 1.95
selling_thresh = 2.5
top_of_hour_share_price = 0
share_price = 1.
shares = 0
buying_power = 25000  # $ Amount in user's account
prev_buying_power = buying_power
share_handler = buying_power / share_price * 0.5 # Amount of shares purchased in one interaction
non_adjustable_min_cash_limit = 4000.
show_closed_status = not check_market_open()

# Exponential Moving average gives weight to recent price changes and captures the movement of trend quickly
ema_twleve = 0    # 12 period
ema_two_six = 0    # 26 period
macd_ema = 0    # 9 period
sma_twelve = []
sma_two_six = []
macd_sma = []

# EMA uses data from days prior to determine new EMA
past_ema_twelve= 0
past_ema_two_six = 0
past_macd_ema = 0

all_share_data = pd.read_csv('ideal_formatted.csv',index_col=False)
username = input('Please enter your username:')
password = input('Please enter your password:')
share_data = []

for index, raw_share_info in all_share_data.iterrows():
    #print(raw_share_info['Volume'])
    if float(raw_share_info['Volume']) > 20000000:
        share_data.append(raw_share_info['Symbol'])
        print(raw_share_info['Symbol'])
try:
    login = stonks.login(username, password, store_session=True)

except:
    print('Invalid login, terminating session')
    raise SystemExit
if login:
    if check_market_open():
        print('Login successful. Accessing user information')


if check_market_open() == False:
    print('Stock market is currently closed')

else:
    print('Stock market is currently open')

for stock in share_data:
    past_close_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='close_price')
    past_low_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='low_price')
    past_high_prices = stonks.get_stock_historicals(stock,interval='day',span='3month',info='high_price')
    current_price = float(stonks.get_latest_price(stock)[0])
    
    for index, low_price in enumerate(past_low_prices[:14]):
        if index == 0:
            lowest_price = float(low_price)
        else:
            if lowest_price > float(low_price):
                lowest_price = float(low_price)
    for index, high_price in enumerate(past_high_prices[:14]):
        if index == 0:
            highest_price = float(high_price)
        else:
            if highest_price > float(high_price):
                highest_price = float(high_price)

    print('Lowest price:', lowest_price)
    print('Highest price:', highest_price)
    print('Current price:', current_price)

while check_market_open():

    for stock in share_data:
        print(stock + ':', stonks.get_stock_historicals(stock,interval='day',span='month',info='close_price'))
        #print(raw_data.values)
        #for stock in raw_data.values:
            #print('Data:', stock[0])
            #share_price.append(stonks.get_fundamentals(stock[0], info='volume'))
            
        #print(share_price)
        #raw_data.insert(1, 'Volume', share_price, True)
        #raw_data.to_csv('new_formatted.csv',index=False)
        
        #my_account = stonks.profiles.load_account_profile()
        #buying_power = my_account['buying_power']
       
        if is_time_interval(hour = 1):
            top_of_hour_share_price = float(share_price[0])

        else: 
            if top_of_hour_share_price == 0:
                top_of_hour_share_price = float(share_price[0]) * 1.21

       
        if is_time_interval(minute=2,second=0):
            if past_ema_twelve != 0 and past_ema_two_six != 0 and past_macd_ema != 0:
                ema_twelve, past_ema_twelve = get_ema(current_value=float(share_price[0]), period=12, past_ema=past_ema_twelve)
                ema_two_six, past_ema_two_six = get_ema(current_value=float(share_price[0]), period=26, past_ema=past_ema_two_six)
                macd_ema, past_macd_ema = get_ema(current_value=(ema_twelve - ema_two_six), period=9, past_ema=past_macd_ema)
            else:
                ema_twelve, sma_twelve = get_ema(current_value=float(share_price[0]), period=12, sma_list=sma_twelve)
                ema_two_six, sma_two_six = get_ema(current_value=float(share_price[0]), period=26, sma_list=sma_two_six)
                macd_ema, macd_sma = get_ema(current_value=(ema_twelve - ema_two_six), period=9, sma_list=macd_sma)

            print('12 period Ema:', ema_twelve, ' sma\'s:', len(sma_twelve))
            print('26 period Ema:', ema_two_six, ' sma\'s:', len(sma_two_six))
            print('9 period Ema:', macd_ema, ' sma\'s:', len(macd_sma))

        if prev_buying_power != buying_power:
            print('Money in account: ',buying_power)
            print('Price of stock:', share_price)
            print('Amount of shares owned:', shares)
            prev_buying_power = buying_power
        
        if past_ema_twelve != 0 and past_ema_two_six != 0 and past_macd_ema != 0:
            macd = ema_twelve - ema_two_six
            macd_histo = macd - macd_ema
            print('MACD Histogram:', macd_histo)
            
            if macd_histo <= macd  and float(share_price[0]) <= .95 * top_of_hour_share_price:
                while buying_power - float(share_price[0]) >= non_adjustable_min_cash_limit:
                    shares += 1
                    buying_power -= float(share_price[0])

                bought_price = float(share_price[0])
        
        if shares != 0:
            if float(share_price[0]) >= 1.05 * bought_price and past_ema_one - past_ema_two >= 0.05:
                    buying_power += shares * float(share_price[0])
                    shares = 0

