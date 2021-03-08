import pandas as pd
import numpy as np
import robin_stocks as stonks
import math

def get_ema(data_frame, current_price, period, past_close_prices):
    '''
    Arguments:
        data_frame = pandas dataframe that contains relevant stock information
        current_price = current price of stock
        period = number of time intervals used for data collection
        past_close_prices = the final share price at the end of 
    '''
    if not pd.isnull(data_frame.iloc[share_index[index_num]]['EMA{}'.format(period)]):
        past_ema = data_frame.iloc[share_index[index_num]]['EMA{}'.format(period)]
        new_ema = current_price * (2 / (period + 1)) + past_ema * (1- (2 / (period + 1)))
    else:
        mov_avg = 0
        for value in past_close_prices[:period]:
            mov_avg += float(value)
        new_ema = mov_avg / period

    all_share_data.loc[share_index[index_num], 'EMA{}'.format(period)] = new_ema
    return new_ema

def get_macd(data_frame, ema_one, ema_two, period, sma_list=[]):
    
    macd = ema_one - ema_two
    if not pd.isnull(data_frame.iloc[share_index[index_num]]['MACD']):
        prev_macd = data_frame.iloc[share_index[index_num]]['MACD']
        macd_signal = macd * (2 / (period + 1)) + prev_macd * (1 - (2 / (period + 1)))
        macd_histo = macd - macd_signal
        #print('MACD Histo:', macd_histo)
        if macd_histo > 0:
            signal = 'BUY'
        elif macd_histo < 0:
            signal = 'SELL'
        
        data_frame_data.loc[share_index[index_num], 'MACD'] = macd_signal
        return signal
    else:
        sma_list.append(macd)
        sma = 0
        for value in sma_list:
            sma += value
        sma /= period
        if len(sma_list) == period:
            data_frame.loc[share_index[index_num], 'MACD'] = sma
    




def get_stochastic(current_price, low_prices, high_prices, period, stochastic_list):
    # %K = (recent closing price - lowest price in period) / (highest price in period - lowest)
    # %D = 3 period SMA of %K
    lowest_price = float(low_prices[0])
    highest_price = float(high_prices[0])
    for price in low_prices[:period]:
        if float(price) < lowest_price:
            lowest_price = float(price)

    for price in high_prices[:period]:
        if float(price) > highest_price:
            highest_price = float(price)
    
    if current_price > highest_price:
        highest_price = current_price
    elif current_price < lowest_price:
        lowest_price = current_price
    percent_k = (current_price - lowest_price) / (highest_price - lowest_price) * 100
   
    stochastic_list = np.append(stochastic_list, percent_k)
    if len(stochastic_list) > 3:
        stochastic_list = np.delete(stochastic_list, 0)

    percent_d = 0
    for value in stochastic_list:
        percent_d += value
    percent_d /= period

    if len(stochastic_list) == period:
        if percent_k >= 80:
            signal = 'SELL'
        elif percent_k - percent_d > 0 and percent_k <= 20:
            signal = 'BUY'
        else:
            signal = 'HOLD'

        return signal, stochastic_list
    else:
        return 'HOLD', stochastic_list

def filter_stocks(data_frame, share_data, share_index):
    print('Filtered out stocks:\n')
    for index, raw_share_info in data_frame.iterrows():
        if float(raw_share_info['Volatility']) > 3 and float(raw_share_info['Volume']) > 5000000:
            share_data.append(raw_share_info['Symbol'])
            share_index.append(index)
            print(raw_share_info['Symbol'])
    return share_data, share_index


def write_volatility(data_frame):
    # Gets volatility of a stock (High volatility = greater price fluctuations)
    for index, new_share_info in data_frame.iterrows():
        print('Writing volatility for:', new_share_info['Symbol'])
        calculated_returns = np.zeros(21)
        deviations = np.zeros(21)
        closing_prices = stonks.get_stock_historicals(new_share_info['Symbol'], interval='day', span='3month', info='close_price')

        for num_index, x in enumerate(closing_prices[:21]):
            if num_index != 0:
                calculated_returns[num_index] = np.log(float(x) / prev_x)
            else:
                calculated_returns[num_index] = float(x)
            prev_x = float(x)
            if calculated_returns[num_index] == 0:
                break
            
        if len(calculated_returns) == 21:
            mean = 0
            for x in calculated_returns:
                mean += float(x)
            mean /= len(calculated_returns)
            for num_index, x in enumerate(calculated_returns):
                deviations[num_index] = x - mean
            variance = 0
            for x in deviations:
                variance += x ** 2
            variance /= len(deviations) - 1
            volatility = math.sqrt(variance)
            data_frame.loc[index, 'Volatility'] = volatility

def write_volume(data_frame):
    for index, new_share_info in data_frame.iterrows():
        print('Writing volume for: ', new_share_info['Symbol'])
        closing_prices = stonks.get_fundamentals(new_share_info['Symbol'], info='average_volume')
        data_frame.loc[index, 'Volume'] = volume
