# crops/train_and_forecast.py

import pandas as pd
import joblib
import numpy as np
from datetime import datetime
from sklearn.ensemble import RandomForestRegressor

# นำเข้าฟังก์ชันจากโมดูล ML ที่เราแยกไว้
from ml.feature_engineering import feature_engineering
from ml.hyperparam_search import gridSearch
from ml.metrics import calc_metrics, metrics_result

# สำหรับการดึงข้อมูลจากฐานข้อมูล CropVariable
# (สมมติว่าใช้ Django ORM ใน context ของ Django shell หรือ management command)
import django
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "price_prediction.settings")
django.setup()

from crops.models import Crop, CropVariable

def get_data_from_db(crop_name):
    """
    ดึงข้อมูลสำหรับ crop ที่ระบุจากตาราง CropVariable
    และแปลงเป็น pandas DataFrame โดยมีคอลัมน์ 'average_price'
    """
    try:
        crop_obj = Crop.objects.get(crop_name=crop_name)
    except Crop.DoesNotExist:
        print(f"ไม่พบ Crop ที่ชื่อ {crop_name}")
        return pd.DataFrame()
    
    qs = CropVariable.objects.filter(crop=crop_obj).order_by('date')
    df = pd.DataFrame(list(qs.values('date', 'average_price')))
    if df.empty:
        return df
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def train_model_for_crop(crop_name):
    """
    กระบวนการเทรนโมเดลสำหรับ crop ที่ระบุ:
      - ดึงข้อมูลจากฐานข้อมูล (CropVariable)
      - ทำ feature engineering
      - แบ่งข้อมูลเป็น Train/Test
      - ใช้ gridSearch เพื่อค้นหาพารามิเตอร์ที่ดีที่สุด
      - เทรนโมเดลและประเมินผล (calculate metrics)
      - บันทึกโมเดลใหม่เป็นไฟล์ .joblib
    """
    # ดึงข้อมูลจากฐานข้อมูลสำหรับ crop ที่ต้องการ
    df_raw = get_data_from_db(crop_name)
    if df_raw.empty:
        print(f"ไม่มีข้อมูลสำหรับ {crop_name}")
        return

    # ทำ feature engineering
    df = feature_engineering(df_raw)
    
    # แบ่งข้อมูลเป็น X, y
    X = df.drop(columns=["average_price", "days"])
    y = df["average_price"]
    train_size = int(len(df) * 0.8)
    X_train, X_test = X[:train_size], X[train_size:]
    y_train, y_test = y[:train_size], y[train_size:]
    
    # สร้างโมเดล RandomForestRegressor เริ่มต้น
    rf = RandomForestRegressor()
    
    # ปรับแต่งพารามิเตอร์ด้วย gridSearch
    best_model = gridSearch(X_train, y_train, rf)
    
    # เทรนโมเดล
    best_model.fit(X_train, y_train)
    
    # ทำนายและคำนวณ metrics
    predictions = best_model.predict(X_test)
    updated_metrics = calc_metrics(y_test, predictions, best_model, name=crop_name, df=metrics_result)
    print("Evaluation Metrics for", crop_name)
    print(updated_metrics)
    
    # รับชื่อไฟล์เพื่อบันทึกโมเดล
    filename = input(f"Enter filename to save the {crop_name} model (without extension): ")
    joblib.dump(best_model, f"{filename}.joblib")
    print(f"Model saved as {filename}.joblib")

if __name__ == "__main__":
    # ตัวอย่าง: เทรนโมเดลสำหรับ crop "ผักคะน้า"
    crop_name = "ผักคะน้า"  # เปลี่ยนเป็นชื่อที่ต้องการเทรน
    train_model_for_crop(crop_name)
