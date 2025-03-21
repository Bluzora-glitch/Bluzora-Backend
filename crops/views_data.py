import pandas as pd
import os
import re
from datetime import datetime
from django.utils.timezone import make_aware
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from .models import Crop, CropVariable

def convert_thai_date(thai_date):
    """ แปลงวันที่ภาษาไทยเป็น YYYY-MM-DD """
    month_map = {
        "ม.ค.": "01", "ก.พ.": "02", "มี.ค.": "03", "เม.ย.": "04",
        "พ.ค.": "05", "มิ.ย.": "06", "ก.ค.": "07", "ส.ค.": "08",
        "ก.ย.": "09", "ต.ค.": "10", "พ.ย.": "11", "ธ.ค.": "12"
    }
    
    try:
        match = re.search(r"(\d{1,2})\s(ม\.ค\.|ก\.พ\.|มี\.ค\.|เม\.ย\.|พ\.ค\.|มิ\.ย\.|ก\.ค\.|ส\.ค\.|ก\.ย\.|ต\.ค\.|พ\.ย\.|ธ\.ค\.)\s(\d{4})", thai_date)
        if not match:
            raise ValueError("รูปแบบวันที่ไม่ถูกต้อง")
        
        day, thai_month, thai_year = match.groups()
        month = month_map.get(thai_month.strip(), None)
        if not month:
            raise ValueError("ไม่พบชื่อเดือนที่ตรงกัน")
        
        year = int(thai_year) - 543  # แปลงปี พ.ศ. → ค.ศ.
        return f"{year}-{month}-{day.zfill(2)}"
    except Exception as e:
        print(f"❌ แปลงวันที่ผิดพลาด: {thai_date} → {e}")
        return None

def update_crop_prices_from_request(request):
    """อ่านไฟล์จาก path ที่กำหนดแล้วอัปโหลดข้อมูล (สำหรับเรียกผ่าน API Django)"""
    file_path = "D:/Bluzora-Backend/price_prediction/prices_downloaded.xls"
    file_name = os.path.basename(file_path)
    success = update_crop_prices(file_path, file_name)  # ✅ ส่งค่าถูกต้อง

    
    if success:
        return JsonResponse({"message": f"นำเข้าข้อมูลจาก {file_name} สำเร็จ!"})
    else:
        return JsonResponse({"error": f"เกิดข้อผิดพลาดในการนำเข้าข้อมูลจาก {file_name}"}, status=400)

def update_crop_prices(file_path, file_name):
    """อัปโหลดข้อมูลราคาพืชจากไฟล์ที่ระบุ"""
    
    if not os.path.exists(file_path):
        print(f"🚫 ไม่พบไฟล์ {file_path}")
        return False

    try:
        df_list = pd.read_html(file_path)
        df = df_list[0]
    except Exception as e:
        print(f"🚫 อ่านไฟล์ {file_name} ไม่ได้: {e}")
        return False
    
    rename_map = {
        'วันที่': 'date',
        'ประเภท': 'category',
        'สินค้า': 'ชื่อสินค้า',
        'หน่วย': 'หน่วย',
        'ราคา ต่ำสุด': 'ราคาต่ำสุด',
        'ราคา สูงสุด': 'ราคาสูงสุด',
        'ราคาเฉลี่ย': 'ราคาเฉลี่ย'
    }
    df.rename(columns=rename_map, inplace=True, errors='ignore')

    try:
        df = df[['date', 'ชื่อสินค้า', 'ราคาเฉลี่ย', 'ราคาต่ำสุด', 'ราคาสูงสุด']]
    except KeyError:
        print(f"🚫 โครงสร้างไฟล์ {file_name} ไม่ถูกต้อง")
        return False

    with transaction.atomic():
        for _, row in df.iterrows():
            crop_name = row['ชื่อสินค้า'].strip()
            avg_price = float(row['ราคาเฉลี่ย'])
            min_price = float(row['ราคาต่ำสุด'])
            max_price = float(row['ราคาสูงสุด'])

            converted_date = convert_thai_date(row['date'].strip())
            if not converted_date:
                continue

            crop, created = Crop.objects.get_or_create(
                crop_name=crop_name,
                defaults={"unit": "กิโลกรัม", "grow_duration": 90}
            )

            CropVariable.objects.update_or_create(
                crop=crop,
                date=converted_date,
                defaults={
                    "average_price": avg_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "file_name": file_name  # ✅ บันทึกว่าไฟล์ไหนอัปโหลดข้อมูลนี้
                }
            )

    print(f"✅ อัปโหลดข้อมูลจาก {file_name} สำเร็จ")
    return True

def update_all_crop_prices(request):
    """สแกนและนำเข้าข้อมูลจากทุกไฟล์ .xls ในโฟลเดอร์"""
    folder_path = "D:/Bluzora-Backend/crops_price/"
    
    if not os.path.exists(folder_path):
        return JsonResponse({"error": "ไม่พบโฟลเดอร์"}, status=400)

    files = [f for f in os.listdir(folder_path) if f.endswith(".xls")]
    if not files:
        return JsonResponse({"error": "ไม่พบไฟล์ .xls ในโฟลเดอร์"}, status=400)

    success_count = 0
    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        if update_crop_prices(file_path, file_name):
            success_count += 1

    return JsonResponse({"message": f"นำเข้าข้อมูลจาก {success_count} ไฟล์สำเร็จ!"})
