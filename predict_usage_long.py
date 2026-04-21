import pandas as pd
import numpy as np
import datetime
import logging
import requests

from sklearn.preprocessing import MinMaxScaler
from tensorflow.python.keras.models import load_model
from collections import OrderedDict

config = tf.compat.v1.ConfigProto()
config.gpu_options.allow_growth = True
session = tf.compat.v1.Session(config=config)

def day_cal(dataset):
    day_list = []

    for i in range(len(dataset)-1):
        if dataset.index[i][0] != dataset.index[i+1][0]:
            day_list.append(i)

    day_list.append(len(dataset))
    return day_list

def remove_cusnum(dataset, cusnum_list):
    remove_list = []
    for i in range(len(cusnum_list)):
        if len(dataset[dataset["CUSNUM"] == cusnum_list[i]]) != 14:
            remove_list.append(cusnum_list[i])

    remove = dataset['CUSNUM'].isin(remove_list)
    dataset = dataset[~remove]
    return dataset

def make_dataset(dataset):
    data = []
    check_list = []
    k = 0
    for i in range(0,len(dataset),14):
        indices = range(i,i+14)
        data.append(dataset[indices])
        k = k+1
        check_list.append(k)
    return np.array(data),check_list

def drop_col(dataset):
    #dataset.drop(['Unnamed: 0'], axis=1, inplace=True)
    dataset.drop(['DAY_OF_WEEK'], axis=1, inplace=True)
    dataset.drop(['MONTH'], axis=1, inplace=True)
    dataset.drop(['DAY'], axis=1, inplace=True)
    dataset.drop(['HOUR'], axis=1, inplace=True)
    return dataset

def scaler(dataset):
    count=0
    k = 0
    scaled_usage_array = np.empty((0,1), dtype=float)
    scaler_usage_list=[]

    for i in range(len(dataset.index)):
        if i < (len(dataset.index) - 1):
            if not dataset.index[i][0] == dataset.index[i+1][0]:
                count = count + 1
                scaled_usage = dataset["USAGE"][k:i+1]
                globals()['scaler_usage_{}'.format(count)] = MinMaxScaler()
                scaled_usage_array = np.append(scaled_usage_array,
                                             globals()['scaler_usage_{}'.format(count)].fit_transform((scaled_usage.values).reshape(-1,1)),
                                            axis=0)
                k = i+1
                scaler_usage_list.append(globals()['scaler_usage_{}'.format(count)])
        else:
            count = count + 1
            scaled_usage = dataset["USAGE"][k:i+1]
            globals()['scaler_usage_{}'.format(count)] = MinMaxScaler()
            scaled_usage_array = np.append(scaled_usage_array,
                                          globals()['scaler_usage_{}'.format(count)].fit_transform((scaled_usage.values).reshape(-1,1)),
                                         axis=0)
            k = i+1
            scaler_usage_list.append(globals()['scaler_usage_{}'.format(count)])

    scaled_usage_array = scaled_usage_array.reshape(-1,)
    return scaled_usage_array, scaler_usage_list

def make_log():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    file_handler = logging.FileHandler('long_predict.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logging.info("Long Term Predict Finish!")

def add_log():
    log_data = OrderedDict()
    log_data["model_id"] = "kr.co.aiblab.waterflow:st_usage_prediction"
    log_data["log_level"] = 1
    log_data["log_message"] = "long prediction test"

    headers = {
        'X-Auth-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJ0ZXN0MDAwMSIsImlhdCI6MTYzNzI5MDAyNX0.FA64aZW42ZFn8weId6yoSXwQn4Zed1ji4hAUZ6oNZ8w',
    }
    request0 = requests.post("http://211.238.12.61:3100/api/models/log", headers=headers, json=log_data)

def main(data):
    test_data = drop_col(data)
    cusnum_list = test_data["CUSNUM"].unique()
    test_data = remove_cusnum(test_data,cusnum_list)
    remove_cusnum_list = test_data["CUSNUM"].unique()
    test_data.set_index(['CUSNUM', "DATE"], drop=False, inplace=True)
    test_data.drop(['DATE'], axis=1, inplace=True)
    test_data.drop(['METERNUM'], axis=1, inplace=True)
    test_data.drop(['CUSNUM'], axis=1, inplace=True)
    test_data = test_data.sort_index(ascending=True)

    scaled_usage_array, scaler_usage_list = scaler(test_data)
    test_data["USAGE"] = scaled_usage_array
    pred_dataset = test_data.values
    pred_day = day_cal(test_data)

    final_x_test, length_test = make_dataset(pred_dataset)
    long_model = load_model('2022_test_long_m.h5')
    pred_y = long_model.predict(final_x_test)

    j = 0
    for i in range(len(length_test)):
        pred_y[j:length_test[i] + 1] = scaler_usage_list[i].inverse_transform(pred_y[j:length_test[i] + 1])
        j = length_test[i]
    pred_y = pred_y.sum(axis=1)

    date = datetime.datetime.now()
    date = date + datetime.timedelta(days=7)
    ymd = datetime.datetime.strftime(date, '%Y-%m-%d')

    result = []
    for i in range(len(pred_y)):
        result.append([{"date": ymd, "usage": str(pred_y[i])}])

    k = 0
    for i in range(len(pred_y)):
        predict_data = OrderedDict()
        predict_data["model_id"] = "kr.co.aiblab.waterflow:st_usage_prediction"
        predict_data["prediction_type"] = 1
        predict_data["cusnum"] = remove_cusnum_list[i]
        predict_data["custype"] = 0
        predict_data["result"] = result[i]
        predict_data = [predict_data]
        headers = {
            'X-Auth-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJ0ZXN0MDAwMSIsImlhdCI6MTYzNzI5MDAyNX0.FA64aZW42ZFn8weId6yoSXwQn4Zed1ji4hAUZ6oNZ8w',
        }
        #request0 = requests.post("http://211.238.12.61:3100/api/prediction/usage/result", headers=headers, json=predict_data)

    print("장기 끝")
if __name__ == '__main__':
    #data = pd.read_csv("2022-10-12_long.csv")
    main()
    #add_log()

