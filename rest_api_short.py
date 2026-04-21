import requests
import pandas as pd
import datetime
import numpy as np
import random
import time


# 날짜 변경 함수
def change_date(date):
    from_datetime = date - datetime.timedelta(days=4)
    to_datetime = date

    fromdate = from_datetime.replace(hour=0, minute=0, second=0)
    todate = to_datetime.replace(hour=0, minute=0, second=0)

    str_fromdate = datetime.datetime.strftime(fromdate, '%Y-%m-%d %H:%M:%S')
    str_todate = datetime.datetime.strftime(todate, '%Y-%m-%d %H:%M:%S')
    return str_fromdate, str_todate

# 전처리 함수
def preprocess_data(data_list):
    meternum = []
    cusnum = []
    date = []
    usage = []
    day_of_week = []
    month = []
    day = []
    hour = []
    preprocess_date = []
    hour_usage = []

    for i in range(len(data_list[1])):
        meternum.append(data_list[1][i]['meternum'])
        cusnum.append(data_list[1][i]['cusnum'])
        date.append(datetime.datetime.strptime(data_list[1][i]['time'], '%Y-%m-%d %H:%M:%S'))
        usage.append(data_list[1][i]['usage'])
        time = datetime.datetime.strptime(data_list[1][i]['time'], '%Y-%m-%d %H:%M:%S')
        day_of_week.append(time.strftime("%A"))
        month.append(time.strftime("%m"))
        day.append(time.strftime("%d"))
        hour.append(time.strftime("%H"))

    for i in range(len(date)):
        preprocess_date.append(date[i].replace(minute=0, second=0))

    # 데이터프레임 생성
    dataframe = pd.DataFrame(data=list(zip(preprocess_date, meternum, cusnum, usage, day_of_week, month, day, hour)),
                             columns=['DATE', 'METERNUM', 'CUSNUM', 'USAGE', 'DAY_OF_WEEK', 'MONTH', 'DAY', 'HOUR'])
    dataframe.set_index(['CUSNUM', "DATE"], drop=False, inplace=True)
    dataframe = dataframe[dataframe["HOUR"] == "23"]
    dataframe = dataframe.sort_index(ascending=True)
    dataframe_values = dataframe.values

    # 시간당 사용량으로 변환
    for i in range(len(dataframe)):
        if dataframe_values[i][1] == dataframe_values[i - 1][1]:
            hour_usage.append(dataframe_values[i][3] - dataframe_values[i - 1][3])
            if i == 0:
                hour_usage.append(None)
        else:
            hour_usage.append(None)

    dataframe["USAGE"] = hour_usage
    dataframe.reset_index(drop=True,inplace=True)
    return dataframe

    # 추후 전처리과정으로 변환 예정

# csv 저장을 위한 이름 정의 함수
def name():
    date = datetime.datetime.now()
    date = date - datetime.timedelta(days=1)
    ymd = datetime.datetime.strftime(date, '%Y-%m-%d')
    return ymd

def json_read(req0, from_date, to_date):
    try:
        json0 = req0.json()
        return json0
    except:
        time.sleep(60)
        headers = {
            'X-Auth-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJ0ZXN0MDAwMSIsImlhdCI6MTYzNzI5MDAyNX0.FA64aZW42ZFn8weId6yoSXwQn4Zed1ji4hAUZ6oNZ8w',
        }
        usage_date0 = {"from": from_date, "to": to_date}
        req0 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date0)
        return json_read(req0, from_date, to_date)

def main():
    global preprocess_data
    global name, path, csv_name

    now_date = datetime.datetime.now()
    from_date, to_date = change_date(now_date)
    print("단기 예측을 위해",from_date,"부터",to_date,"까지 사용")

    headers = {
        'X-Auth-token': 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyaWQiOiJ0ZXN0MDAwMSIsImlhdCI6MTYzNzI5MDAyNX0.FA64aZW42ZFn8weId6yoSXwQn4Zed1ji4hAUZ6oNZ8w',
    }
    usage_date = {"from": from_date, "to": to_date}
    req0 = requests.post("http://211.238.12.61:3100/api/waterflows/r-meterdata/historyAll", headers=headers, data=usage_date)

    json_data = json_read(req0, from_date, to_date)
    original_realtime = list(json_data.values())

    predata = preprocess_data(original_realtime)
    predata = predata.dropna()
    print("전체가구 : ", len(predata['CUSNUM'].unique()))

    #데이터 부족한 cusnum 삭제
    from_datetime = now_date - datetime.timedelta(days=4)
    to_datetime = now_date
    fromdate = from_datetime.replace(hour=0, minute=0, second=0)
    todate = to_datetime.replace(hour=0, minute=0, second=0)
    delta = todate - fromdate

    cusnum_list = predata['CUSNUM'].unique()
    cusnum_list2 = []

    for i in range(len(cusnum_list)):
        if len(predata[predata["CUSNUM"] == cusnum_list[i]]) < delta.days-1:
            cusnum_list2.append(cusnum_list[i])

    remove_cusnum2 = predata['CUSNUM'].isin(cusnum_list2)
    predata = predata[~remove_cusnum2]
    predata.reset_index(drop=True, inplace=True)
    print("최종 예측가구 : ", len(predata['CUSNUM'].unique()))

    csv_name = name()
    #path = "C:\\Users\\choiyoungjun\\Desktop\\"
    #path = "./lp-usage-predict/data"
    csv_name = csv_name + "_short.csv"
    #path = path + csv_name
    #predata.to_csv(csv_name)
    return predata, csv_name

if __name__ == '__main__':
    main()
    print("저장완료 : ", csv_name)
