import numpy as np
import pandas as pd
import os
from functools import reduce

def preprocess(filepath:str, save_to:str=None, standardlize_factors:list=None, timesteps:int=7):
    filename = os.path.basename(filepath)
    if filename[filename.rfind('.'):] != '.csv':
        raise Exception('Support only csv file.')
    if not os.path.exists(filepath):
        raise Exception('File not found.')
    if save_to != None:
        if not os.path.exists(save_to):
            raise Exception('can not find save directory')
    timesteps = timesteps if timesteps >= 2 else 2
    df = pd.read_csv(filepath)
    df.insert(0, 'Labels', df['Close'].values)
    stocks = df
    stocks['ZScoreMidPrice'] = (stocks['High']+stocks['Low'])/2.0
    # Standardlization
    if type( standardlize_factors ) != type( None ):
        if len(standardlize_factors) == 6:
            midprice_mean, midprice_std, open_mean, open_std, close_mean, close_std = standardlize_factors
        else:
            raise Exception('Wrong standardlize_factors.')
    else:
        midprice_mean, midprice_std = stocks['ZScoreMidPrice'].mean(), stocks['ZScoreMidPrice'].std()
        open_mean, open_std = stocks['Open'].mean(), stocks['Open'].std()
        close_mean, close_std = stocks['Close'].mean(), stocks['Close'].std()
        standardlize_factors = midprice_mean, midprice_std, open_mean, open_std, close_mean, close_std
    stocks['ZScoreMidPrice'] = (stocks['ZScoreMidPrice']-midprice_mean)/midprice_std
    stocks['Open'] = (stocks['Open']-open_mean)/open_std
    stocks['Close'] = (stocks['Close']-close_mean)/close_std
    stocks = stocks.drop(columns=['Date', 'Adj Close', 'Volume', 'High', 'Low'])
    if 'Ticker' in df:
        # multiple stocks
        stocks = stocks.groupby(['Ticker'])
        stock_name = []
        stocks_df_list = []
        for name, group in stocks:
            stock_name.append(name)
            stock = group.drop(columns=['Ticker']).to_numpy()
            stocks_df_list.append(stock[:len(stock)//timesteps*timesteps].reshape((len(stock)//timesteps, timesteps, 4))) # trim samples to make it able to devide by timesteps timesteps
        reduce_stocks = reduce(lambda a, b: np.concatenate((a, b)), stocks_df_list) # concate all stock into single array
        reduce_stocks = reduce_stocks if len(reduce_stocks)%2 == 0 else reduce_stocks[:-1] # trim list to make its length equal to even number
        all_data = reduce_stocks
        features, labels = reduce_stocks[0::2][:,:,2], reduce_stocks[1::2][:,:,0] # only select ZScoreMidPrice as a feature
        features = np.expand_dims(features, axis=1) # bc it have only 1 feature the shape will be change, need to expand dim to keep the shape as the same
    else:
        # single stock
        stock = stocks.to_numpy()
        stock = stock[:len(stock)//timesteps*timesteps].reshape((len(stock)//timesteps, timesteps, 4))
        stock = stock if len(stock)%2 == 0 else stock[:-1]
        all_data = stock
        features, labels = stock[0::2][:,:,2], stock[1::2][:,:,0]
        features = np.expand_dims(features, axis=1) # bc it have only 1 feature the shape will be change, need to expand dim to keep the shape as the same
    if save_to != None:
        save_path = os.path.join(save_to, filename[:filename.rfind('.')]+f'-{timesteps}ts-preprocessed.npz')
        with open(save_path, 'wb') as f:
            np.savez(f, all_data=all_data, features=features, labels=labels, standardlize_factors=standardlize_factors)
        return save_path, all_data, features, labels, standardlize_factors
    else:
        return all_data, features, labels, standardlize_factors

def get_volumes(filepath:str):
    filename = os.path.basename(filepath)
    if filename[filename.rfind('.'):] != '.csv':
        raise Exception('Support only csv file.')
    if not os.path.exists(filepath):
        raise Exception('File not found.')
    volumes = None
    try:
        volumes = pd.read_csv(filepath)['Volume'].values
    except Exception as e:
        print(f'Error while reading csv file {e}')
    return volumes
