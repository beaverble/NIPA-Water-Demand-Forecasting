import requests
import pandas as pd
import datetime
import time
from dateutil.relativedelta import *
import rest_api_short
import logging
from collections import OrderedDict

def change_date(date):
    from_datetime = date - relativedelta(months=1)
    middle_datetime = date - relativedelta(months=1)
    to_datetime = date

    fromdate = from_datetime.replace(day=1, hour=0, minute=0, second=0)
    middledate = from_datetime.replace(hour=0, minute=0, second=0)
    todate = to_datetime.replace(hour=0, minute=0, second=0)
    fromdate = fromdate - datetime.timedelta(days=1)
    middle_end = middledate + datetime.timedelta(days=1)
    middle_start = middledate

    str_fromdate = datetime.datetime.strftime(fromdate, '%Y-%m-%d %H:%M:%S')
    str_todate = datetime.datetime.strftime(todate, '%Y-%m-%d %H:%M:%S')
    str_middleend = datetime.datetime.strftime(middle_end, '%Y-%m-%d %H:%M:%S')
    str_middlestart = datetime.datetime.strftime(middle_start, '%Y-%m-%d %H:%M:%S')
    return str_fromdate, str_middleend, str_middlestart, str_todate

def cal_total_usage(excessive_data):
    count = 0
    cusnum = []
    total_usage = []
    now_date = datetime.datetime.now()

    for i in range(len(excessive_data) - 1):
        if excessive_data['DATE'][i].month == now_date.month - 1:
            if not excessive_data['CUSNUM'][i] == excessive_data['CUSNUM'][i + 1]:
                total_usage.append(sum(excessive_data["USAGE"][count:i]))
                count = i
                cusnum.append(excessive_data['CUSNUM'][i])
            if i == len(excessive_data) - 2:
                total_usage.append(sum(excessive_data["USAGE"][count:i + 2]))
                cusnum.append(excessive_data['CUSNUM'][i])

    return cusnum, total_usage

def cal_excessive(total_usage):
    total_price = []
    excessive_grade = []
    for i in range(len(total_usage)):
        if total_usage[i] <= 50:
            price = 860 + (total_usage[i] * 620)
            total_price.append(price)
            excessive_grade.append(1)
        elif total_usage[i] <= 100:
            price = 860 + ((50 * 620) + ((total_usage[i] - 50) * 850))
            total_price.append(price)
            excessive_grade.append(2)
        else:
            price = 860 + ((50 * 620) + (50 * 850) + ((total_usage[i] - 100) * 1040))
            total_price.append(price)
            excessive_grade.append(3)

    return total_price, excessive_grade

def json_read(req0,req1,from_date,middle_end,middle_start,to_date):
    try:
        time.sleep(60)
        print("request start!")
        json0 = req0.json()
        json1 = req1.json()
        print("request end!")
        return json0, json1
    except:
        print("request except!")
        time.sleep(60)
        headers = {
            'X-Auth-token': '',
        }
        usage_date0 = {"from": from_date, "to": middle_end}
        usage_date1 = {"from": middle_start, "to": to_date}
        req0 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date0)
        req1 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date1)
        return json_read(req0, req1, from_date, middle_end, middle_start, to_date)

def add_log():
    log_data = OrderedDict()
    log_data["model_id"] = "kr.co.aiblab.waterflow:st_usage_prediction"
    log_data["log_level"] = 1
    log_data["log_message"] = "excessive prediction test"
    log_data = log_data

    headers = {
        'X-Auth-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJ0ZXN0MDAwMSIsImlhdCI6MTYzNzI5MDAyNX0.FA64aZW42ZFn8weId6yoSXwQn4Zed1ji4hAUZ6oNZ8w',
    }
    request0 = requests.post("http://211.238.12.61:3100/api/models/log", headers=headers, json=log_data)
    return request0

def make_log():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    file_handler = logging.FileHandler('excessive_predict.log')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logging.info("excessive Predict Finish!")
    return


def main():
    now_date = datetime.datetime.now()
    from_date,middle_end,middle_start, to_date = change_date(now_date)

    headers = {
        'X-Auth-token': '',
    }
    usage_date0 = {"from": from_date, "to": middle_end}
    usage_date1 = {"from": middle_start, "to": to_date}
    print(usage_date0)
    print(usage_date1)

    req0 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date0)
    req1 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date1)

    json0, json1 = json_read(req0, req1, from_date, middle_end, middle_start, to_date)

    original_realtime0 = list(json0.values())
    original_realtime1 = list(json1.values())

    predata0 = rest_api_short.preprocess_data(original_realtime0)
    predata0 = predata0.dropna()

    predata1 = rest_api_short.preprocess_data(original_realtime1)
    predata1 = predata1.dropna()

    excessive_data = pd.concat([predata0, predata1])
    excessive_data.set_index(["CUSNUM", 'DATE'], drop=False, inplace=True)
    #print(excessive_data)

    cusnum, total_usage = cal_total_usage(excessive_data)
    #print(cusnum)
    total_price, total_grade = cal_excessive(total_usage)

    last_month_usage = []
    this_month_usage = []

    for i in range(len(cusnum)):
        final_excessive_data = excessive_data.loc[cusnum[i]]
        last_excessive = excessive_data[(excessive_data['CUSNUM'] == cusnum[i]) &
                                        (excessive_data['MONTH'] == str(now_date.month - 1).zfill(2))]
        this_excessive = excessive_data[(excessive_data['CUSNUM'] == cusnum[i]) &
                                        (excessive_data['MONTH'] == str(now_date.month).zfill(2))]
        last_month_usage.append(last_excessive["USAGE"][0:now_date.day].sum())
        this_month_usage.append((this_excessive["USAGE"][0:now_date.day - 1].sum()))

    percent_list = []
    pred_total_usage = []
    for i in range(len(last_month_usage)):
        percent = ((this_month_usage[i] - last_month_usage[i]) / this_month_usage[i]) * 100
        percent_list.append(percent)
        pred_total_usage.append(total_usage[i] + (total_usage[i] * (percent_list[i] * 0.01)))

    pred_price, pred_grade = cal_excessive(pred_total_usage)

    result = []
    for i in range(len(pred_price)):
        result.append([{"progressive_grade": pred_grade[i], "progressive_tax": str(pred_price[i])}])

    k = 0
    for i in range(len(pred_price)):
        predict_data = OrderedDict()
        predict_data["model_id"] = "kr.co.aiblab.waterflow:excessive_usage_prediction"
        predict_data["cusnum"] = cusnum[i]
        predict_data["result"] = result[i]
        headers = {
            'X-Auth-token': '',
        }
        request0 = requests.post("http://211.238.12.61:3100/api/prediction/excessive_usage/result", headers=headers, json=predict_data)
        print("excessive model prediction finish")

if __name__ == '__main__':
    main()
    #make_log()
    add_log()
