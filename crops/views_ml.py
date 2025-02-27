import os
import joblib
import pandas as pd
from datetime import date, timedelta
from django.http import JsonResponse
from django.db import transaction
from .models import Crop, CropVariable, PredictedData
from .ml.feature_engineering import feature_engineering
from .ml.recursive_forecast import recursive_forecast

def get_data_from_db(crop_name):
    try:
        crop_obj = Crop.objects.get(crop_name=crop_name)
    except Crop.DoesNotExist:
        return pd.DataFrame()

    qs = CropVariable.objects.filter(crop=crop_obj).order_by('date')
    df = pd.DataFrame(list(qs.values('date', 'average_price')))

    if df.empty:
        return df

    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    return df

def forecast_and_save(request):
    # Mapping ระหว่างชื่อพืชกับไฟล์โมเดล
    models_mapping = {
        "ผักคะน้า คละ": "crops/ml_models/kana_rf_grid.joblib",
        "ผักชี คละ (บาท/กก.)": "crops/ml_models/pakchee_rf_grid.joblib",
        "ผักกวางตุ้ง คละ": "crops/ml_models/kuangthung_rf_grid.joblib"
    }

    with transaction.atomic():
        for crop_name, model_path in models_mapping.items():
            # โหลดโมเดล
            if not os.path.exists(model_path):
                print(f"ไม่พบไฟล์โมเดล {model_path}")
                continue
            rf_model = joblib.load(model_path)

            # ดึงข้อมูลจาก DB แทนการอ่าน CSV
            df_raw = get_data_from_db(crop_name)
            if df_raw.empty:
                print(f"ไม่มีข้อมูลใน DB สำหรับ {crop_name}")
                continue

            df_features = feature_engineering(df_raw)
            if df_features.empty:
                print(f"ข้อมูล {crop_name} หลัง feature_engineering ว่างเปล่า")
                continue
            
            # พยากรณ์ 90 วัน
            forecast_result = recursive_forecast(df_features, rf_model, 90)

            # บันทึกผลลงใน PredictedData
            crop_obj = Crop.objects.get(crop_name=crop_name)
            for forecast_date, row in forecast_result.iterrows():
                PredictedData.objects.update_or_create(
                    crop=crop_obj,
                    predicted_date=forecast_date,
                    defaults={"predicted_price": row['predicted_price']}
                )

    return JsonResponse({"message": "พยากรณ์และบันทึกข้อมูลสำเร็จ!"})
