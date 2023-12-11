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
import share_manager as stonk_calc
import tradingview_ta as sa  # Stonk Analysis
import urllib.request, urllib.error, urllib.parse
from fuzzywuzzy import fuzz
import keyboard
import random
from datetime import datetime
import pytz
import pyotp
import pyautogui
from discord_client import Client


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
  
  config = get_directory('config.txt')
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
  discord_watch = Client()
  discord_watch.register_window()
  discord_watch.set_active()
  
  can_buy = True
  can_sell = True
  # Buys and sells stocks within the first busiest hour of the day
  if first_hour:
    if int(time_tracker) <= 1030 or int(time_tracker) > 1600:
      time_start = '0930'
      time_end = '1020'
    else:
      time_start = '1450'
      time_end = '1550'
  else:
    time_end = '1550'

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
    if successful_login:
      if check_market_open():
        print('Login successful. Accessing {} information\n'.format(user +
                                                                    '\'s'))
        if is_sim:
          print('Running {}\'s bot in simulation mode\n'.format(user))
        else:
          print('Running {}\'s bot in regular mode\n'.format(user))
        print('Stock market is currently open\n')
        if int(time_tracker) >= int(time_end) + 10:
          print(
            'Busiest trading hour has passed. {} is waiting to start trading at {} on the next trading day...\n\n'
            .format(user, time_start))
      else:
        print('Login successful. Accessing {} information\n'.format(user +
                                                                    '\'s'))
        if is_sim:
          print('Running {}\'s bot in simulation mode\n'.format(user))
        else:
          print('Running {}\'s bot in regular mode\n'.format(user))
        print(
          'Stock market is currently closed. {} is waiting to start trading at {} on the next trading day...\n\n'
          .format(user, time_start))
      
      # Gets some user/sim info and initializes some variables for using TradingView
      buying_power = float(stonks.load_account_profile(
        info='buying_power'))  # $ Amount in user's account
      prev_buying_power = buying_power
      sim_money = buying_power
      prev_sim_money = sim_money
      sim_min_cash_limit = non_adjustable_min_cash_limit
      holdings = stonks.build_holdings()
      exchange = 'nasdaq'
      screener = 'america'
      stocks_updated = False
      if is_master:
        time.sleep(2)
        logout = stonks.logout()
        
      discord_command = ""
      refresh_command = False
      while discord_command != "kill":
        
        timeInNewYork = datetime.now(newYorkTz)
        time_tracker = timeInNewYork.strftime("%H%M")
        discord_command = discord_watch.check_discord()
        
        if stocks_updated:
          while check_market_open() and int(time_tracker) <= int(time_end) + 10 and discord_command != "kill":
            timeInNewYork = datetime.now(newYorkTz)
            time_tracker = timeInNewYork.strftime("%H%M")
            
            discord_command = discord_watch.check_discord()
            if discord_command == "refresh":
                refresh_command = True
                can_buy = False
            if len(holdings) == 0 and refresh_command:
                share_data = []
                formatted_stocks = refresh_stocks(stock_url, stock_path_two, all_share_data)
                for i in range(num_stocks):
                    share_data.append(formatted_stocks[i])
                can_buy = True
                refresh_command = False
                    
            if is_time_interval(second=wait_time):
              if len(share_data) == 0:
                formatted_stocks = refresh_stocks(stock_url, stock_path_two, all_share_data)
                for i in range(num_stocks):
                    share_data.append(formatted_stocks[i])
              for index_num, stock in enumerate(share_data):
                handler = sa.TA_Handler(symbol=stock,
                                        screener=screener,
                                        exchange=exchange,
                                        interval=interval)
                stock_exists = True
                try:
                  stock_data = handler.get_analysis()
                except:
                  print(stock, 'is not available on Trading View')
                  share_data.pop(share_data.index(stock))
                  stock_exists = False
                
                if stock_exists:
                  macd_signal = stock_data.oscillators['COMPUTE']['MACD']
                  signal_2 = stock_data.moving_averages['COMPUTE']['EMA10']
                  # signal_3 = calc_rsi(2,stonks.stocks.get_stock_historicals(stock,) How do I want to feed 2 days worth of close prices (hourly,10min,etc.)
                  current_price = float(stonks.get_latest_price(stock)[0])
                  share_handler = math.floor(
                    (buying_power - non_adjustable_min_cash_limit) /
                    current_price * percent_buy /
                    100)  # Amount of shares purchased in one interaction
                  if share_handler < 1:
                    share_handler = 1

                  if is_sim:
                    share_handler = math.floor(
                      (sim_money - sim_min_cash_limit) / current_price *
                      percent_buy /
                      100)  # Amount of shares purchased in one interaction
                    if share_handler < 1:
                      share_handler = 1

                  # Prevents buying stocks that cannot be sold once day trading limit is reached for the week or at the end of the trading day for regular day trading
                  is_error = True
                  while is_error:
                    # Sometimes there is a 502 Server Error for getting day trades causing program to crash, this remedies that
                    try:

                      if (mode == 'regular' and
                          3 - len(stonks.get_day_trades('equity_day_trades')) -
                          trades <= 0) or (
                            first_hour and int(time_tracker) < int(time_start)
                            or int(time_tracker) >= 1550):
                        if can_buy:
                          print(
                            '{} is no longer making purchases. Waiting to sell stocks...'
                            .format(user))
                        can_buy = False

                      else:
                        can_buy = True
                      is_error = False
                    except:
                      pass

                  if holdings.get(stock) is not None and can_sell:  # If you have ANY stocks, allows you to sell them

                    if mode == 'day trade':
                      if int(time_tracker) >= int(time_end):
                        if is_sim:
                          prev_sim_money = sim_money
                          perform_transaction('SELL', stock, float(holdings[stock]['quantity']), sim_money, current_price, is_sim, user)
                          sim_money += float(holdings[stock]['quantity']) * current_price
                          holdings.pop(stock)  # Allows for artificial removing of stocks
                        else:
                          perform_transaction('SELL', stock, float(holdings[stock]['quantity']),buying_power, current_price, is_sim, user)
                          buying_power = float(stonks.load_account_profile(info='buying_power'))
                          holdings = stonks.build_holdings()
                      else:
                          
                          if current_price > float(holdings[stock]['average_buy_price']) * 1.02:
                            if macd_signal != 'BUY' and past_signal_2[index_num] != 'BUY':
                                perform_transaction('SELL', stock, float(holdings[stock]['quantity']),buying_power, current_price, is_sim, user)
                                buying_power = float(stonks.load_account_profile(info='buying_power'))
                                holdings = stonks.build_holdings()
                          elif current_price < float(holdings[stock]['average_buy_price']):
                            perform_transaction('SELL', stock, float(holdings[stock]['quantity']),buying_power, current_price, is_sim, user)
                            buying_power = float(stonks.load_account_profile(info='buying_power'))
                            holdings = stonks.build_holdings()
                        # if macd_signal == 'SELL' and past_signal_2[index_num] == 'SELL' and not is_sim:
                        #   perform_transaction('SELL', stock, float(holdings[stock]['quantity']),buying_power, current_price, is_sim, user)
                        #   buying_power = float(stonks.load_account_profile(info='buying_power'))
                        #   holdings = stonks.build_holdings()
                        # elif is_sim and macd_signal == 'SELL' and past_signal_2[index_num] == 'SELL':
                        #   prev_sim_money = sim_money
                        #   perform_transaction('SELL', stock, float(holdings[stock]['quantity']),sim_money, current_price, is_sim, user)
                        #   sim_money += float(holdings[stock]['quantity']) * current_price

                        #   holdings.pop(stock)
                    else:

                      if macd_signal == 'SELL' and past_signal_2[index_num] == 'SELL' and current_price > float(holdings[stock]['average_buy_price']) and not is_sim:
                        perform_transaction('SELL', stock,
                                            float(holdings[stock]['quantity']),
                                            buying_power, current_price,
                                            is_sim, user)
                        buying_power = float(stonks.load_account_profile(info='buying_power'))
                        holdings = stonks.build_holdings()
                      elif is_sim and macd_signal == 'SELL' and past_signal_2[index_num] == 'SELL':
                        prev_sim_money = sim_money
                        perform_transaction('SELL', stock,
                                            float(holdings[stock]['quantity']),
                                            sim_money, current_price, is_sim,
                                            user)
                        sim_money += float(holdings[stock]['quantity']) * current_price
                        holdings.pop(stock)

                  elif holdings.get(stock) is None:
                    if can_buy:
                        # if current_price > float(holdings[stock]['average_buy_price']) * 1.05:
                        #     perform_transaction('BUY', stock, share_handler,
                        #                     buying_power, current_price,
                        #                     is_sim, user)
                        #     buying_power = float(
                        #     stonks.load_account_profile(info='buying_power'))
                        #     holdings = stonks.build_holdings()
                        #     trades += 1
                      if macd_signal == 'BUY' and past_signal_2[
                          index_num] == 'BUY' and buying_power - (
                            share_handler * current_price
                          ) >= non_adjustable_min_cash_limit and not is_sim:
                        perform_transaction('BUY', stock, share_handler,
                                            buying_power, current_price,
                                            is_sim, user)
                        buying_power = float(
                          stonks.load_account_profile(info='buying_power'))
                        holdings = stonks.build_holdings()
                        trades += 1
                      elif is_sim and macd_signal == 'BUY' and past_signal_2[
                          index_num] == 'BUY' and sim_money - (
                            share_handler *
                            current_price) >= sim_min_cash_limit:
                        new_stock = {
                          stock: {
                            'price': str(current_price),
                            'quantity': str(share_handler),
                            'average_buy_price': str(current_price)
                          }
                        }  # Artificially creates new stock data
                        prev_sim_money = sim_money
                        perform_transaction('BUY', stock, share_handler,
                                            sim_money, current_price, is_sim,
                                            user)
                        sim_money -= share_handler * current_price
                        holdings.update(
                          new_stock
                        )  # Artificially adds new stock data to holdings
                        trades += 1

                  past_signal_2[index_num] = signal_2
          stocks_updated = False
          buy_only = False
          if first_hour:
            if int(time_tracker) > 1020 and int(time_tracker) <= 1550:
              buy_only = True
              sell_only = False
              time_start = '1450'
              time_end = '1550'
            else:
              buy_only = False
              sell_only = True
              time_start = '0930'
              time_end = '1020'

          timeInNewYork = datetime.now(newYorkTz)
          time_now = timeInNewYork.strftime("%b %d %Y")
          if not check_market_open():
            print(
              'Stock market is now closed. {} is waiting to start trading at {} on the next trading day...\n'
              .format(user, time_start))
          else:
            print(
              'End of busiest trading hour. {} is waiting to start trading at {} on the next trading day...\n'
              .format(user, time_start))
          if is_sim:
            print('{}\'s net money for today: $'.format(user) +
                  str(sim_money - init_money))
            output = 'Net cash for {}: $'.format(time_now) + str(
              sim_money - init_money) + '\n'
            logger('.//Quamez\'s Bot//simulated net profit.txt', output)
          else:
            buying_power = float(
              stonks.load_account_profile(info='buying_power'))
            print('{}\'s net money for today: $'.format(user) +
                  str(buying_power - init_money))
            output = 'Net cash for {}: $'.format(time_now) + str(
              buying_power - init_money) + '\n'
            logger(get_directory('net profit.txt'), output)

        else:

          # At the beginning of the day, filter the most volatile stocks (Pretty accurate if I do say so myself)
          if check_market_open() and int(time_tracker) >= int(
              time_start) and int(time_tracker) <= int(time_end) + 10:
            print('Stock market open.\n')
            trades = 0
            can_buy = True

            if is_sim:
              init_money = sim_money
            else:
              # Uses authenticator app in order to perform Robinhood logins
              totp = pyotp.TOTP(two_factor).now()
              login = stonks.login(username, password, mfa_code=totp)
              buying_power = float(
                stonks.load_account_profile(info='buying_power'))
              init_money = buying_power

            # Pulls info from Trading View website to get stocks to invest in for the day
            if first_hour:
              if int(time_tracker) < 1030 or int(time_tracker) > 1550:
                time_start = '0930'
                time_end = '1020'
                can_sell = True
                can_buy = False
              else:
                time_start = '1450'
                time_end = '1550'
                can_sell = False
                can_buy = True
            else:
              time_end = '1550'

            formatted_stocks = refresh_stocks(stock_url, stock_path_two,
                                              all_share_data)
            print('Filtering new stocks.')
            login = stonks.login(username, password, mfa_code=totp)
            if not is_sim:
              holdings = stonks.build_holdings(
              )  # used for getting info of currently owned shares

            stocks_owned = [None]
            share_data = []
            if len(holdings) > 0:
              num_stocks = num_stocks - len(holdings)
              for index, x in enumerate(holdings.keys()):  # returns the list of stock tickers that are currently being invested in
                if stocks_owned[index] is None:
                  stocks_owned[index] = x
                  stocks_owned.append(None)
                else:
                  stocks_owned.append(x)
            else:
              stocks_owned = [None]
            
            try:
              for i in range(num_stocks):
                share_data.append(formatted_stocks[i])
            except:
              for i in range(len(formatted_stocks)):
                share_data.append(formatted_stocks[i])
            for index, x in enumerate(
                holdings.keys()
            ):  # returns the list of stock tickers that are currently being invested in
              is_duplicate = False
              for y in range(len(share_data)):
                if x == share_data[y]:
                  is_duplicate = True

              if not is_duplicate:
                share_data.append(x)

            print('\n{}\'s stocks for the day:'.format(user))
            for x in share_data:
              print(x)

            #share_data = stonk_calc.filter_stocks(all_share_data, share_data, num_stocks,1,30000,2, buying_power=buying_power,owned_stocks=stocks_owned)
            stocks_updated = True
            stocks_owned = [None]
            past_signal_2 = np.full(num_stocks + len(holdings), 'None') # Past signals used to lag the first signal
            print('Transactions for the day:\n')
      print("Code ended with \"stop\" command")
