import tensorflow as tf
import pandas as pd
import numpy as np
import datetime
import predict_usage_short
from dateutil.relativedelta import *
from tensorflow.python.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.python.keras.models import load_model

def set_gpu_memory_growth(enable=True):
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        print("GPU is available!")
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, enable)
            logical_gpus = tf.config.list_logical_devices('GPU')
            print(len(gpus), "Physical GPUs,", len(logical_gpus), "Logical GPUs")
        except RuntimeError as e:
            print(e)
    else:
        print("GPU is NOT AVAILABLE!")

def train_test_time():
    now_time = datetime.datetime.now()
    test_end = now_time.replace(hour=0, minute=0, second=0)
    test_end_text = datetime.datetime.strftime(test_end, '%Y-%m-%d %H:%M:%S')
    test_start = datetime.datetime.strftime(test_end - relativedelta(months=1), '%Y-%m-%d %H:%M:%S')
    train_end = datetime.datetime.strftime(test_end - relativedelta(months=1), '%Y-%m-%d %H:%M:%S')
    train_start =datetime.datetime.strftime(test_end - relativedelta(months=3), '%Y-%m-%d %H:%M:%S')
    return train_start, train_end, test_start, test_end_text

def make_dataset(dataset, target, history_size, cusnum_len, day, target_size):
    data = []
    labels = []
    check_point = 0
    check_list = []
    k = 0

    for i in range(cusnum_len):
        start_index = check_point + history_size
        end_index = day[i]

        for j in range(start_index, end_index, 1):
            if j + target_size <= end_index:
                indices = range(j - history_size, j)
                data.append(dataset[indices])
                labels.append(target[j:j + target_size])
                check_point = end_index
                k = k + 1
            else:
                break

        check_list.append(k)

    return np.array(data), np.array(labels), check_list

def main(dataframe):
    #데이터 전처리
    set_gpu_memory_growth()
    realtime_data = predict_usage_short.drop_col(dataframe)
    realtime_data.set_index(['METERNUM', "DATE"], drop=False, inplace=True)
    realtime_data.drop(['DATE'], axis=1, inplace=True)
    realtime_data.drop(['METERNUM'], axis=1, inplace=True)
    realtime_data.drop(['CUSNUM'], axis=1, inplace=True)
    realtime_data = realtime_data.sort_index(ascending=True)

    scaled_usage_array, scaler_usage_list = predict_usage_short.scaler(realtime_data)
    realtime_data["USAGE"] = scaled_usage_array

    # 학습데이터,테스트데이터 분리
    train_start, train_end, test_start, test_end = train_test_time()
    idx = pd.IndexSlice
    train_data = realtime_data.loc[idx[:, train_start:train_end], :]
    test_data = realtime_data.loc[idx[:, test_start:test_end], :]

    realtime_train_dataset = train_data.values
    realtime_test_dataset = test_data.values

    train_day = predict_usage_short.day_cal(realtime_train_dataset)
    test_day = predict_usage_short.day_cal(realtime_test_dataset)

    # 학습데이터, 테스트데이터 생성
    shift_days = 14
    shift_steps = shift_days
    future_target = 7

    final_x_train, final_y_train, length_train = make_dataset(realtime_train_dataset, realtime_train_dataset[:, 0],
                                                              shift_steps, len(scaler_usage_list), train_day, future_target)

    final_x_test, final_y_test, length_test = make_dataset(realtime_test_dataset, realtime_test_dataset[:, 0],
                                                           shift_steps, len(scaler_usage_list), test_day, future_target)

    # 모델 학습
    early_stopping = EarlyStopping(monitor='val_loss', patience=10, verbose=1)
    path_checkpoint = '2022_long_normal.h5'
    callback_checkpoint = ModelCheckpoint(filepath=path_checkpoint, monitor='val_loss', verbose=1, save_weights_only=False, save_best_only=True)
    model = load_model('2022_test_long_m.h5')
    model.fit(final_x_train, final_y_train, validation_data=(final_x_test, final_y_test), batch_size=128,
              epochs=1000, verbose=2, callbacks=[early_stopping, callback_checkpoint])
    model.save('2022_test_long_m.h5')

if __name__ == '__main__':
    main()