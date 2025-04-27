import pandas as pd
import os
import re
from datetime import datetime
from django.utils.timezone import make_aware
from django.http import JsonResponse
from django.db import transaction, IntegrityError
from .models import Crop, CropVariable
from django.shortcuts import render

# ฟังก์ชันสำหรับแสดงหน้าแรก
def home(request):
    return render(request, 'home.html')

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
    """
    อ่านไฟล์จาก path ที่กำหนด โดยรับชื่อไฟล์จาก query parameter
    (เช่น /update-prices/?file=prices_downloaded.xls) และอัปโหลดข้อมูล
    สำหรับเรียกผ่าน API Django
    ไฟล์ที่อัปโหลดได้จะอยู่ในโฟลเดอร์ crops_price
    """
    # รับชื่อไฟล์จาก query parameter 'file'
    file_name = request.GET.get('file')
    if not file_name:
        return JsonResponse({"error": "กรุณาระบุชื่อไฟล์ xls ผ่านพารามิเตอร์ 'file'"}, status=400)
    
    # กำหนด base path ที่เก็บไฟล์ในโฟลเดอร์ crops_price
    base_path = "D:/Bluzora-Backend/crops_price/"
    file_path = os.path.join(base_path, file_name)
    
    success = update_crop_prices(file_path, file_name)
    
    if success:
        return JsonResponse({"message": f"นำเข้าข้อมูลจาก {file_name} สำเร็จ!"})
    else:
        return JsonResponse({"error": f"เกิดข้อผิดพลาดในการนำเข้าข้อมูลจาก {file_name}"}, status=400)


def update_crop_prices(file_path, file_name):
    """
    อัปโหลดข้อมูลราคาพืชจากไฟล์ที่ระบุ พร้อมคืนสรุปแถวที่ถูกข้าม (เนื่องจากมีค่า nan)
    คืนค่ากลับเป็น tuple (success, skipped_summary) โดย skipped_summary เป็น dictionary
    ที่มีรายละเอียดเป็น list ของ dict สำหรับแต่ละแถวที่ถูกข้าม: 
      {"crop": ชื่อพืช, "date": วันที่, "skipped_count": จำนวนที่ข้าม (ถ้ากลุ่มเดียวกัน)}
    """
    if not os.path.exists(file_path):
        print(f"🚫 ไม่พบไฟล์ {file_path}")
        return False, {"error": "ไม่พบไฟล์"}

    try:
        df_list = pd.read_html(file_path)
        df = df_list[0]
    except Exception as e:
        print(f"🚫 อ่านไฟล์ {file_name} ไม่ได้: {e}")
        return False, {"error": str(e)}
    
    # เปลี่ยนชื่อคอลัมน์ให้ตรงตามที่เราต้องการ
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
        return False, {"error": "โครงสร้างไฟล์ไม่ถูกต้อง"}
    
    skipped_entries = []  # รายการแถวที่ข้ามไปเนื่องจากมีค่า nan

    with transaction.atomic():
        for _, row in df.iterrows():
            crop_name = row['ชื่อสินค้า'].strip()
            raw_date = row['date'].strip()
            
            # ตรวจสอบว่าค่าราคาต่าง ๆ เป็น valid number หรือไม่
            if pd.isna(row['ราคาเฉลี่ย']) or pd.isna(row['ราคาต่ำสุด']) or pd.isna(row['ราคาสูงสุด']):
                print(f"⚠️ ข้อมูลราคาของ {crop_name} ในวันที่ {raw_date} ไม่สมบูรณ์ ข้ามแถว")
                skipped_entries.append((crop_name, raw_date))
                continue

            try:
                avg_price = float(row['ราคาเฉลี่ย'])
                min_price = float(row['ราคาต่ำสุด'])
                max_price = float(row['ราคาสูงสุด'])
            except Exception as e:
                print(f"⚠️ ไม่สามารถแปลงราคาของ {crop_name} ในวันที่ {raw_date}: {e}")
                skipped_entries.append((crop_name, raw_date))
                continue

            converted_date = convert_thai_date(raw_date)
            if not converted_date:
                print(f"⚠️ ไม่สามารถแปลงวันที่ {raw_date} สำหรับ {crop_name} ข้ามแถว")
                skipped_entries.append((crop_name, raw_date))
                continue

            # บันทึกข้อมูลลงใน Crop (หรือสร้างใหม่หากไม่พบ)
            crop, created = Crop.objects.get_or_create(
                crop_name=crop_name,
                defaults={"unit": "กิโลกรัม", "grow_duration": 90}
            )
            
            # อัปเดตหรือสร้างข้อมูลใน CropVariable
            CropVariable.objects.update_or_create(
                crop=crop,
                date=converted_date,
                defaults={
                    "average_price": avg_price,
                    "min_price": min_price,
                    "max_price": max_price,
                    "file_name": file_name  # บันทึกว่าไฟล์ไหนเป็นแหล่งข้อมูล
                }
            )
    
    # สรุป skipped_entries ให้เป็นรูปแบบ grouped โดย (crop, date)
    skipped_summary = {}
    for crop, date_str in skipped_entries:
        key = (crop, date_str)
        if key in skipped_summary:
            skipped_summary[key] += 1
        else:
            skipped_summary[key] = 1

    # แปลงให้เป็น list ของ dict สำหรับส่งออก
    skipped_list = []
    for (crop, date_str), count in skipped_summary.items():
        skipped_list.append({
            "crop": crop,
            "date": date_str,
            "skipped_rows": count
        })

    print(f"✅ อัปโหลดข้อมูลจาก {file_name} สำเร็จ")
    return True, {"skipped_records": skipped_list}


def update_all_crop_prices(request):
    """
    สแกนและนำเข้าข้อมูลจากทุกไฟล์ .xls ในโฟลเดอร์ พร้อมสรุปแถวที่ถูกข้ามในแต่ละไฟล์
    สรุปจะมีไฟล์, ชื่อพืช, วันที่ และจำนวนแถวที่ถูกข้าม (เนื่องจากมีค่า nan)
    """
    folder_path = "D:/Bluzora-Backend/crops_price/"
    
    if not os.path.exists(folder_path):
        return JsonResponse({"error": "ไม่พบโฟลเดอร์"}, status=400)
    
    files = [f for f in os.listdir(folder_path) if f.endswith(".xls")]
    if not files:
        return JsonResponse({"error": "ไม่พบไฟล์ .xls ในโฟลเดอร์"}, status=400)
    
    success_count = 0
    overall_skipped = {}  # key: file_name, value: list of skipped record details

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        success, file_skipped_summary = update_crop_prices(file_path, file_name)
        if success:
            success_count += 1
        overall_skipped[file_name] = file_skipped_summary.get("skipped_records", [])
    
    return JsonResponse({
        "message": f"นำเข้าข้อมูลจาก {success_count} ไฟล์สำเร็จ!",
        "skipped_summary": overall_skipped
    })

