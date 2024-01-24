'''
Created by: Quamez Anderson
Date Created: 08 February 2021
'''

import robin_stocks.robinhood as stonks
import time
import os
import pandas as pd
import numpy as np
import math
#import share_manager as stonk_calc
import tradingview_ta as sa  # Stonk Analysis
import urllib.request, urllib.error, urllib.parse
import keyboard
import random
from datetime import datetime
import pytz
import pyotp
import pyautogui
import fuzzywuzzy as fuzz
import tensorflow as tf
import tensorflow_hub as hub
#from discord_client import Client
import tensorflow as tf
import tensorflow_hub as hub

print('TF version:', tf.__version__)
print('TF Hub Version:', hub.__version__)
# Check for GPU availability
print('GPU', 'available' if tf.config.list_physical_devices('GPU') else 'not available')

class AITrader():
    def __init__(self, symbol="AAPL", is_crypto = False, is_paper = True):
        self.symbol = symbol
        self.cash = float(stonks.load_account_profile(
            info='buying_power'))
        self.is_crypto = is_crypto
        self.paper_trading = is_paper
        if not self.is_crypto:
          self.data = pd.DataFrame([float(x) for x in stonks.get_stock_historicals(self.symbol,interval='hour',span='year',info='close_price')])[0]
        else:
          self.data = pd.DataFrame([float(x) for x in stonks.get_crypto_historicals(self.symbol,interval='day',span='year',info='close_price')])[0]

    def calculate_ema(self,period):
        ema = self.data.ewm(span=period,adjust=False).mean()
        return ema
    
    def calculate_macd(self):
      macd = self.calculate_ema(12) - self.calculate_ema(26)
      signal = macd.ewm(span=9,adjust=False).mean()
      return macd, signal
    
    def get_last_year(self):
      historicals = pd.DataFrame()
      historicals['EMA12'] = self.calculate_ema(12)
      macd,signal = self.calculate_macd()
      historicals["MACD_S"] = macd - signal
      for x in range(len(self.data)):
        if x != len(self.data) - 1:
          if self.data[x] > self.data[x+1]: # If this days close price is higher than next day's SELL
            historicals.loc[x, 'Signal'] = 1
          elif self.data[x] < self.data[x+1]: # If this days close price is lower than next day's BUY
            historicals.loc[x, 'Signal'] = 2
          else:
            historicals.loc[x, 'Signal'] = 0
        else:
          historicals.loc[x, 'Signal'] = 0
      
      return historicals
    
    def convert_one_hot(self,one_hot): # Used for converting a one hot vector to an action (really only used for seeing a training guess)
      for x in range(3):
        if one_hot[x] == 1:
          if x == 0:
            return "HOLD"
          elif x == 1:
            return "SELL"
          elif x == 2:
            return "BUY"


      
def check_market_open():
  '''
    Trading hours are from 0930 to 1600
    '''
  newYorkTz = pytz.timezone("America/New_York")
  timeInNewYork = datetime.now(newYorkTz)
  time_tracker = timeInNewYork.strftime("%H%M")
  current_day = time.strftime("%A")
  if current_day != 'Saturday' and current_day != 'Sunday':
    if ((int(time_tracker) >= 930) and int(time_tracker) < 1600):
      return True
    else:
      return False
  else:
    return False


def is_time_interval(
    minute=-1,
    hour=-1,
    second=-1):  # Checks current time every specified time interval
  current_hour = time.strftime("%H")
  current_min = time.strftime("%M")
  current_sec = time.strftime("%S")
  if minute != -1:
    if hour == -1:
      minute_check = int(current_min) % minute == 0
    else:
      minute_check = int(current_min) == 0
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


def logger(filename, output):
  with open(filename, 'a') as f:
    f.write(output)


def perform_transaction(transaction, symbol, shares, buying_power,
                        current_price, is_sim, user):
  newYorkTz = pytz.timezone("America/New_York")
  timeInNewYork = datetime.now(newYorkTz)
  current_time = timeInNewYork.strftime("%b %d %Y %H:%M:%S")
  prev_buying_power = buying_power
  if shares != 0: # Prevents occasional error where 0 gets passed since you can't fulfill a buy or sell order of 0 shares
      if transaction == 'BUY':
        print('\n{} is buying'.format(user), shares, 'shares for:', symbol, '\n')
        if not is_sim:
          order = stonks.order_buy_fractional_by_quantity(symbol, shares)
        else:
          buying_power -= shares * current_price
        action = 'bought'
      elif transaction == 'SELL':
        print('\n{} is selling'.format(user), shares, 'shares for:', symbol, '\n')
        if not is_sim:
          order = stonks.order_sell_fractional_by_quantity(symbol, shares)
        else:
          buying_power += shares * current_price
        action = 'sold'
      if not is_sim:
        #print(order)
        print('Waiting for order to go in')
        while buying_power == prev_buying_power:
          buying_power = float(stonks.load_account_profile(info='buying_power'))
          time.sleep(1)
        print('Order complete')
      output = 'Time:{}\nStock:{}\nTransaction:{} shares {} for ${} each for a total of ${}\nPrevious buying power:{}\nBuying power:{}\n\n'.format(
        current_time, symbol, shares, action, current_price,
        current_price * shares, prev_buying_power, buying_power)
      if not is_sim:
        directory = get_directory('transactions.txt')
      else:
        directory = get_directory('simulated transactions.txt')
      logger(directory, output)


def load_config(
  file
):  # Allows for easier configuration of code. See config file for what method returns and in what order
  params = []
  with open(file) as f:
    for line in f.readlines():
      data = ''
      for index, character in enumerate(line):
        if index > line.index(':'):
          data += character
      data = str.strip(data)
      params.append(data)
  f.close()
  params[2] = float(params[2])
  params[7] = int(params[7])
  params[9] = float(params[9])
  params[10] = int(params[10])

  if params[4] == 'Volatility':
    params[
      4] = 'https://www.tradingview.com/markets/stocks-usa/market-movers-most-volatile/'
  elif params[4] == 'Top Gainer':
    params[
      4] = 'https://www.tradingview.com/markets/stocks-usa/market-movers-gainers/'
  elif params[4] == 'Top Loser':
    params[
      4] = 'https://www.tradingview.com/markets/stocks-usa/market-movers-losers/'

  if params[5] == 'Yes':
    params[5] = True
  elif params[5] == 'No':
    params[5] = False
  if params[14] == 'Yes':
    params[14] = True
  elif params[14] == 'No':
    params[14] = False

  return params


def check_key(
  key, user
):  # If user key has expired or is invalid, they need to re-purchase a new key
  newYorkTz = pytz.timezone("America/New_York")
  timeInNewYork = datetime.now(newYorkTz)
  date_today = timeInNewYork.strftime("%m%d%Y")
  date_to_check = ''
  try:
    if key[29] == 'A':
      date_to_check = str(int(key[2]) - 1) + key[6] + str(
        int(key[7]) - 4) + key[13] + str(int(key[18]) - 1) + str(
          int(key[22]) - 2) + str(int(key[24]) - 5) + key[28]
    elif key[29] == 'B':
      date_to_check = '0' + key[6] + str(int(key[7]) - 4) + key[13] + str(
        int(key[18]) - 1) + str(int(key[22]) - 2) + str(int(key[24]) -
                                                        5) + key[28]

    if int(date_today) > int(date_to_check) or int(
        date_today[6] + date_today[7]) > int(date_to_check[6] +
                                             date_to_check[7]):
      print(
        'Expired or invalid key given for {}. Terminating session.\n'.format(
          user))
      return 'invalid'
    else:
      print(
        'Token accepted for {}. Thank you for using Priscilla.\n'.format(user))
      return 'valid'
  except:
    print('Expired or invalid key given for {}. Terminating session.\n'.format(
      user))
    return 'invalid'


def get_directory(
  file_name
):  # Returns the path for a given file (used for config, perform_transaction, stock_run)
  directory = __name__.replace('bot.', '')
  directory = directory.capitalize()
  directory = directory + '\'s Bot//' + file_name
  directory = './/' + directory
  return directory


def refresh_stocks(stock_url, stock_path_two, all_share_data):  # Only really used for initializing all of the lists for user data
  
  print("Refreshing stocks")
  site = urllib.request.urlopen(stock_url)
  web_content = site.read().decode('UTF-8')
  should_loop = True
  while should_loop:  # Removes the circle element from the symbols causing reading inaccuracies
    deleted = False
    if web_content.find('<span class=\"tv-cir') != -1:
        web_content = remove_html_tags(web_content, '<span class=\"tv-cir',
                                        '</span>')
        deleted = True

    if not deleted:
        should_loop = False
  f = open(stock_path_two, 'w', encoding='utf-8')
  f.write(web_content)
  f.close()
  html_data = pd.read_html(stock_path_two)[0]

  raw_stocks = []
  for i in html_data['Symbol']:
    x = ''
    for y in range(len(i)):
      if y < 4 and i[y].isupper():
        x += i[y]
      elif y == 5 or i[y].islower():
        raw_stocks.append(x)
        break

  formatted_stocks = []
  for i in raw_stocks:
    ratios = []
    for j in all_share_data['Symbol']:
      ratios.append((fuzz.token_set_ratio(i, j)))
    if max(ratios) >= 95:
      stock_to_be_added = ratios.index(
        max(ratios
            ))  # Returns the index of the stock that is the most likely match
      formatted_stocks.append(all_share_data['Symbol'][stock_to_be_added])

  return formatted_stocks


def remove_html_tags(text, tag1, tag2):
  original_text = text
  init_index = original_text.find(tag1)
  end_index = original_text[init_index:].find(tag2) + len(tag2)
  new_text = original_text[:init_index] + original_text[init_index +
                                                        end_index:]
  return new_text


  
  

def stock_run(time_delay, is_master):
  
  config = 'Quamez\'s Bot\config.txt'
  username, password, percent_buy, time_start, stock_url, is_sim, interval, wait_time, mode, non_adjustable_min_cash_limit, num_stocks, stock_path, stock_path_two, bot_key, first_hour, two_factor = load_config(
    config)
  user = __name__.replace('bot.', '').capitalize()
  bot_key = check_key(bot_key, user)
  newYorkTz = pytz.timezone(
    "America/New_York")  # Uses a standardized timezone for the entire server
  timeInNewYork = datetime.now(newYorkTz)
  time_tracker = timeInNewYork.strftime("%H%M")
  all_share_data = pd.read_csv(stock_path, index_col=False)
  # Used for determining the times the bot will start and stop during the trading day

  # Allows for remote access through discord commands
  #discord_watch = Client()
  #discord_watch.register_window()
  #discord_watch.set_active()

  if bot_key == 'valid':
    successful_login = False
    try:
      # Uses a Time-Based One Time Password in order for users other than myself to use bot
      totp = pyotp.TOTP(two_factor).now()
      login = stonks.login(username, password, mfa_code=totp)
      successful_login = True

    except:
      print('Invalid login, terminating session for', user)
    
    # Display info for logging in
    # if successful_login:
    #   if check_market_open():
    #     print('Login successful. Accessing {} information\n'.format(user +
    #                                                                 '\'s'))
    #     if is_sim:
    #       print('Running {}\'s bot in simulation mode\n'.format(user))
    #     else:
    #       print('Running {}\'s bot in regular mode\n'.format(user))
    #     print('Stock market is currently open\n')
    #     if int(time_tracker) >= int(time_end) + 10:
    #       print(
    #         'Busiest trading hour has passed. {} is waiting to start trading at {} on the next trading day...\n\n'
    #         .format(user, time_start))
    #   else:
    #     print('Login successful. Accessing {} information\n'.format(user +
    #                                                                 '\'s'))
    #     if is_sim:
    #       print('Running {}\'s bot in simulation mode\n'.format(user))
    #     else:
    #       print('Running {}\'s bot in regular mode\n'.format(user))
    #     print(
    #       'Stock market is currently closed. {} is waiting to start trading at {} on the next trading day...\n\n'
    #       .format(user, time_start))
      
    # Initializes AITrader object
    symbol = "DOGE"
    trader = AITrader(symbol, True)

    # Get past year's worth of data for symbol
    

    #newest_index = len(historicals['EMA12'])
    # Constantly calculate today's ema, macd, macd_s to compare against previous
    #if trader.is_crypto:
      #trader.data[newest_index] = float(stonks.get_crypto_quote(symbol,info="mark_price"))
    #else:
      #trader.data[newest_index] = float(stonks.get_latest_price(symbol))

    tech_indicators = trader.get_last_year()
    print(tech_indicators)
    signal = tech_indicators.pop('Signal')
    signal = tf.one_hot(signal, 3)
    TEST_INDEX = random.randint(0,len(signal)-1)
    test = pd.DataFrame(data=[[tech_indicators['EMA12'][TEST_INDEX], tech_indicators['MACD_S'][TEST_INDEX]]],columns=['EMA12', 'MACD_S'])
    tech_indicators = tf.convert_to_tensor(tech_indicators)
    INPUT_SHAPE = [None, len(tech_indicators), 2,]
    
    normalizer = tf.keras.layers.Normalization(axis=-1)
    normalizer.adapt(tech_indicators)
    model = tf.keras.Sequential([
      normalizer,
      tf.keras.layers.Dense(32, activation='relu'),
      tf.keras.layers.Dense(50, activation='relu'),
      tf.keras.layers.Dense(3, activation='softmax')
    ])
    
    
    model.compile(optimizer='adam',
                  loss=tf.keras.losses.CategoricalCrossentropy(),
                  metrics=['accuracy'])
    
    model.build(INPUT_SHAPE)
    model.fit(x=tech_indicators, y=signal, epochs=5000, batch_size=32)
    
    print(model.predict(test))
    action = np.argmax(model.predict(test))
    if action == 1:
      print("SELL")
    elif action == 2:
      print("BUY")
    else:
      print("HOLD")
    print("Actual:", trader.convert_one_hot(signal[TEST_INDEX]))
    

      