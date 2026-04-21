import schedule
import time
import os
import rest_api_short
import rest_api_long
import predict_usage_short
import predict_usage_long
import predict_usage_short_retrain
import predict_usage_long_retrain

def main_short():
   pre_data_short, path_short = rest_api_short.main()
   predict_usage_short.main(pre_data_short)
   predict_usage_short.add_log()

def main_long():
   pre_data_long, path_long = rest_api_long.main()
   predict_usage_long.main(pre_data_long)
   predict_usage_long.add_log()

def main_excessive():
   os.system("python predict_excessive_final.py")

def main_retrain(data0,data1):
   predict_usage_short_retrain.main(data0)
   predict_usage_long_retrain.main(data1)

if __name__ == '__main__':
   schedule.every().day.at("00:00").do(main_short)
   schedule.every().day.at("00:05").do(main_long)
   schedule.every().day.at("00:10").do(main_excessive)
   #schedule.every(12).weeks.do(main_retrain)

   main_short()
   main_long()
   main_excessive()
   #pre_data_short, path_short = rest_api_short.main()
   #pre_data_long, path_long = rest_api_long.main()
   #main_retrain(pre_data_long,pre_data_long)

   while True:
      schedule.run_pending()
      time.sleep(1)


