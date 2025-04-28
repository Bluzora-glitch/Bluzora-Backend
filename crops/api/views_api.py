from rest_framework import viewsets
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_date
from django.db.models import F
from django.http import JsonResponse
from crops.models import Crop, CropVariable, PredictedData
from .filters import CropVariableFilter, PredictedDataFilter
from .serializers import CropSerializer, CropVariableSerializer, PredictedDataSerializer
import os
from django.conf import settings
from django.core.files import File
from django.core.files.storage import default_storage



import math

class CropVariablePagination(PageNumberPagination):
    page_size = 100  # หรือกำหนดตามที่ต้องการ

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    http_method_names = ['get']  # รองรับเฉพาะ GET

class CropVariableViewSet(viewsets.ModelViewSet):
    queryset = CropVariable.objects.all()
    serializer_class = CropVariableSerializer
    pagination_class = CropVariablePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CropVariableFilter
    http_method_names = ['get']  # รองรับเฉพาะ GET

class PredictedDataViewSet(viewsets.ModelViewSet):
    queryset = PredictedData.objects.all()
    serializer_class = PredictedDataSerializer
    pagination_class = CropVariablePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PredictedDataFilter
    http_method_names = ['get']  # รองรับเฉพาะ GET

@api_view(['GET'])
def crops_list(request):
    """
    ส่งรายชื่อพืชทั้งหมดในรูปแบบ JSON โดยใช้ JsonResponse พร้อม ensure_ascii=False 
    เพื่อให้ภาษาไทยแสดงผลได้ถูกต้อง
    """
    crops = Crop.objects.all()
    serializer = CropSerializer(crops, many=True)
    data = serializer.data
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response

@api_view(['GET'])
def combined_price_forecast(request):
    """
    Endpoint รวมข้อมูล Historical และ Predicted
    พร้อมคำนวณ Overall Summary:
      - overall_average, overall_min, overall_max: ถ้ามี historical ใช้ historical,
        ไม่มีก็ใช้ predicted
      - volatility_percent: คำนวณจากข้อมูล historical (ถ้ามี) ไม่มีก็ใช้ predictedแทน
      - price_change_percent: คำนวณจากราคาที่ใกล้เคียง start_date และ end_date
    """
    # รับ query parameter
    vegetable_name = request.GET.get('vegetableName')
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')
    
    if not (vegetable_name and start_date_str and end_date_str):
        return Response({"error": "Missing parameters"}, status=400)
    
    # แปลงวันที่
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    if not (start_date and end_date):
        return Response({"error": "Invalid date format"}, status=400)
    
    # ทำความสะอาดชื่อพืชและหา Crop Object
    vegetable_name_clean = vegetable_name.strip()
    crop_obj = Crop.objects.filter(crop_name__icontains=vegetable_name_clean).first()
    if not crop_obj:
        return Response({"error": "Crop not found"}, status=404)
    
    crop_name = crop_obj.crop_name
    
    # Query historical data จาก CropVariable
    historical_qs = CropVariable.objects.filter(
        crop=crop_obj,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'average_price', 'min_price', 'max_price').order_by('date')
    
    # Query predicted data จาก PredictedData
    predicted_qs = PredictedData.objects.filter(
        crop=crop_obj,
        predicted_date__gte=start_date,
        predicted_date__lte=end_date
    ).values('predicted_date', 'predicted_price')
    
    # สร้าง list สำหรับ Historical
    historical = [
        {
            "crop_name": crop_name,
            "date": str(item['date']),
            "min_price": float(item['min_price']),
            "max_price": float(item['max_price']),
            "price": float(item['average_price']),
            "type": "historical"
        }
        for item in historical_qs
    ]
    
    # สร้าง list สำหรับ Predicted
    predicted = [
        {
            "crop_name": crop_name,
            "date": str(item['predicted_date']),
            "price": float(item['predicted_price']),
            "type": "predicted"
        }
        for item in predicted_qs
    ]
    
    # รวมข้อมูลทั้งสองชุด แล้วเรียงลำดับตามวันที่
    combined = historical + predicted
    combined.sort(key=lambda x: (x['date'], 0 if x['type'] == "historical" else 1))
    
    # สร้าง combined_price_list โดยรวมราคาจาก historical และเพิ่ม predicted สำหรับวันที่หลังสุดของ historical
    last_hist_date = None
    if historical:
        last_hist_date = max(parse_date(item['date']) for item in historical)
    
    combined_price_dict = {}
    for item in historical:
        combined_price_dict[item['date']] = float(item['price'])
    for item in predicted:
        p_date = parse_date(item['date'])
        if last_hist_date is None or p_date > last_hist_date:
            combined_price_dict[item['date']] = float(item['price'])
    
    combined_price_list = []
    for date_str in sorted(combined_price_dict.keys()):
        combined_price_list.append({
            "crop_name": crop_name,
            "date": date_str,
            "combined_price": combined_price_dict[date_str]
        })
    
    # ---------------------------------------------------
    # คำนวณ Overall Summary
    # ---------------------------------------------------
    # หากมี historical data ให้ใช้ historical_qs; ถ้าไม่มีใช้ predicted_qs
    if historical_qs.exists():
        data_source = list(historical_qs)
        avg_prices = [float(item['average_price']) for item in data_source if item['average_price'] is not None]
        min_prices = [float(item['min_price']) for item in data_source if item['min_price'] is not None]
        max_prices = [float(item['max_price']) for item in data_source if item['max_price'] is not None]
        prices_for_vol = [
            {"date": item['date'], "price": float(item['average_price'])}
            for item in data_source if item['average_price'] is not None
        ]
    elif predicted_qs.exists():
        data_source = list(predicted_qs)
        avg_prices = [float(item['predicted_price']) for item in data_source if item['predicted_price'] is not None]
        # ไม่มี min/max แยกใน predicted, ใช้ predicted_price ทั้งหมด
        min_prices = avg_prices[:]  # copy list
        max_prices = avg_prices[:]
        prices_for_vol = [
            {"date": item['predicted_date'], "price": float(item['predicted_price'])}
            for item in data_source if item['predicted_price'] is not None
        ]
    else:
        avg_prices = []
        min_prices = []
        max_prices = []
        prices_for_vol = []
    
    overall_avg = sum(avg_prices) / len(avg_prices) if avg_prices else 0.0
    overall_min = min(min_prices) if min_prices else 0.0
    overall_max = max(max_prices) if max_prices else 0.0
    
    volatility_percent = 0.0
    if len(prices_for_vol) >= 2:
        volatility_percent = _calculate_volatility_from_prices(prices_for_vol)
    
    # คำนวณ Price Change Percent จากราคาที่ใกล้เคียง start_date และ end_date
    start_price = _get_closest_price(crop_obj, start_date)
    end_price = _get_closest_price(crop_obj, end_date)
    price_change_percent = 0.0
    if start_price != 0:
        price_change_percent = ((end_price - start_price) / start_price) * 100
    
    overall_summary = {
        "overall_average": round(overall_avg, 2),
        "overall_min": round(overall_min, 2),
        "overall_max": round(overall_max, 2),
        "volatility_percent": round(volatility_percent, 2),
        "price_change_percent": round(price_change_percent, 2)
    }
    
    return JsonResponse(
        {
            "results": combined,
            "combined": combined_price_list,
            "overall_summary": overall_summary
        },
        json_dumps_params={'ensure_ascii': False},
        charset='utf-8',
    )

def _calculate_volatility_from_prices(prices):
    """
    คำนวณความผันผวน (Volatility) จากข้อมูลราคาที่ได้รับ
    ขั้นตอน:
      1. เรียงข้อมูลตามวันที่
      2. คำนวณผลตอบแทนรายวัน = (price[i] - price[i-1]) / price[i-1]
      3. คำนวณ Standard Deviation ของผลตอบแทน
      4. แปลงเป็นเปอร์เซ็นต์
    """
    if len(prices) < 2:
        return 0.0
    sortedPrices = sorted(prices, key=lambda x: x["date"])
    returns = []
    for i in range(1, len(sortedPrices)):
        prev_price = sortedPrices[i-1]["price"]
        curr_price = sortedPrices[i]["price"]
        if prev_price > 0:
            returns.append((curr_price - prev_price) / prev_price)
    if len(returns) < 2:
        return 0.0
    avg_return = sum(returns) / len(returns)
    variance = sum((r - avg_return) ** 2 for r in returns) / (len(returns) - 1)
    volatility = math.sqrt(variance)
    return volatility * 100

def _get_closest_price(crop_obj, target_date):
    """
    หา average_price ของ CropVariable ที่ใกล้ target_date ที่สุด
    โดยพิจารณาทั้งข้อมูลก่อนและหลัง target_date แล้วเลือกอันที่ใกล้ที่สุด
    """
    before_or_equal = CropVariable.objects.filter(
        crop=crop_obj,
        date__lte=target_date
    ).order_by('-date').first()
    
    after = CropVariable.objects.filter(
        crop=crop_obj,
        date__gte=target_date
    ).order_by('date').first()
    
    candidate = None
    if before_or_equal and after:
        diff_before = abs((target_date - before_or_equal.date).days)
        diff_after = abs((after.date - target_date).days)
        candidate = before_or_equal if diff_before <= diff_after else after
    elif before_or_equal:
        candidate = before_or_equal
    elif after:
        candidate = after
    
    if candidate:
        return float(candidate.average_price or 0.0)
    return 0.0

# --------------------------------------------------
# One-time migration endpoint to re-upload local images to Cloudinary
# --------------------------------------------------
@api_view(['GET'])
def migrate_images(request):
    """
    Migrate existing local media files to Cloudinary based on a filename->crop_name mapping.
    """
    # ตารางแม็ปไฟล์ -> ชื่อพืช
    FILE_MAP = {
        "vegetables-2202487_1280.jpg":   "ผักคะน้า คละ",
        "Untitled_design.png":            "ผักกวางตุ้ง คละ",
        "pshdqhqvvakkbh3zevrh.webp":     "ผักชี คละ (บาท/กก.)",
        "ตนหอม_UpDZtwv.jpg":            "ต้นหอม คละ (บาท/กก.)",
        "ดไซนทยงไมไดตงชอ_3.png":       "ผักบุ้งจีน คละ",
        "salad-3480650_1280.jpg":        "ผักกาดหอม คละ",
        "tomato-9390177_1280.webp":      "มะเขือเทศผลใหญ่ คละ",
        "ขนฉาย_PSaAyqq.jpg":            "ขึ้นฉ่าย คละ (บาท/กก.)",
        "crop_images/พรกชฟา.jpg":        "พริกสดชี้ฟ้า (บาท/กก.)",
        "tomato-9390177_1280_0laA3tA.webp": "มะเขือเทศผลใหญ่ คัด",
        "แตงกวา_iNSxduA.jpg":           "แตงกวา คัด",
        "แตงกวา.jpg":                    "แตงกวา คละ",
        "image-1549402831451_omjzegj.jpg": "ฟักเขียว คัด",
        "image-1549402831451.jpg":       "ฟักเขียว คละ",
        "ดไซนทยงไมไดตงชอ_6_pxuFunJ.png":"หัวผักกาด คัด",
        "ดไซนทยงไมไดตงชอ_6.png":        "หัวผักกาด คละ",
        "ดไซนทยงไมไดตงชอ_1.png":        "กะหล่ำดอก คัด",
        "กะหลำดอก1.png":                 "กะหล่ำดอก คละ",
        "ดไซนทยงไมไดตงชอ_2.png":        "กะหล่ำปลี คัด",
        "green-1939664_1280.jpg":         "กะหล่ำปลี คละ",
        "vegetables-2202487_1280_S4Ms9oN.jpg":"ผักคะน้า คัด",
        "MG_0442-Selected-1024x683.jpg":   "ข้าวโพดฝักอ่อน",
        "ดไซนทยงไมไดตงชอ_8.png":        "ขิงแก่",
        "Young-ginger-raw.jpg":           "ขิง อ่อน",
        "กระชายขาว.jpg":                 "กระชายขาว คละ",
        "ดไซนทยงไมไดตงชอ_5_oJINbbC.png":"หน่อไม้ฝรั่ง คัด",
        "ดไซนทยงไมไดตงชอ_5.png":        "หน่อไม้ฝรั่ง คละ",
        "Untitled_design_3rkh959.png":     "ผักกวางตุ้ง คัด",
        "ขนฉาย_fNS6M9m.jpg":              "ขึ้นฉ่าย คัด (บาท/ขีด)",
        "ขนฉาย_xq9XkYg.jpg":              "ขึ้นฉ่าย คัด (บาท/กก.)",
        "ขนฉาย_NEoz0nd.jpg":              "ขึ้นฉ่าย คละ (บาท/ขีด)",
        "ดไซนทยงไมไดตงชอ_7.png":         "มะนาว เบอร์ 1-2",
        "ดไซนทยงไมไดตงชอ_7_uGB4m6A.png": "มะนาว เบอร์ 3-4",
        "มะเขอเปราะ-Thai-egg-plant-1024x809.jpg.webp":"มะเขือเจ้าพระยา",
        "631100000136_Spu6DS8.jpg":        "มะระจีน คัด",
        "631100000136.jpg":                "มะระจีน คละ",
        "Product_50019_124385316_fullsize_RDFuryQ.jpg":"ผักบุ้งไทย (10 กำ)",
        "Product_50019_124385316_fullsize.jpg":"ผักบุ้งไทย",
        "ดไซนทยงไมไดตงชอ_3_oYjRrID.png":"ผักบุ้งจีน คัด",
        "pshdqhqvvakkbh3zevrh_AppmGgn.webp":"ผักชี คัด (บาท/ขีด)",
        "pshdqhqvvakkbh3zevrh_WO2h4FR.webp":"ผักชี คัด (บาท/กก.)",
        "pshdqhqvvakkbh3zevrh_CaL3VuZ.webp":"ผักชี คละ (บาท/ขีด)",
        "salad-3480650_1280_y5sdPJS.jpg":"ผักกาดหอม คัด",
        "ดไซนทยงไมไดตงชอ_10_uaJPjLI.png":"ผักกาดขาว (ลุ้ย) คัด",
        "ดไซนทยงไมไดตงชอ_10.png":"ผักกาดขาว (ลุ้ย) คละ",
        "ดไซนทยงไมไดตงชอ_9.png":"ผักกะเฉด",
        "cc9jqbeuvipprtvvotve.png":"มะละกอ (พันธุ์แขกดำดำเนิน) คละ",
        "image-1549403069110_fNvM5u6.jpg":"พริกขี้หนูจินดา (แดง) (บาท/ขีด)",
        "image-1549403069110.jpg":"พริกขี้หนูจินดา (แดง) (บาท/กก.)",
        "5dfafc56595344c18993b0e1377c29b9.webp":"พริกขี้หนูสวน (เม็ดกลาง)",
        "9d924846bd04e5d69e90674d54b8d384.jpg":"พริกสดชี้ฟ้า (บาท/ขีด)",
        "ดไซนทยงไมไดตงชอ_4_QzUM6Ro.png":"มะเขือเทศสีดา คัด",
        "ดไซนทยงไมไดตงชอ_4.png":"มะเขือเทศสีดา คละ",
        "ตนหอม_1_3qcaJcN.jpg":"ต้นหอม คัด (บาท/ขีด)",
        "ตนหอม_1_MOsz2as.jpg":"ต้นหอม คัด (บาท/กก.)",
        "ตนหอม_1.jpg":"ต้นหอม คละ (บาท/ขีด)",
        "yardlong-bean-5642281_1280_Z7Elnzg.jpg":"ถั่วฝักยาว คัด",
        "yardlong-bean-5642281_1280.jpg":"ถั่วฝักยาว คละ",
    }

    results = []
    media_root = settings.MEDIA_ROOT  # โฟลเดอร์ media ของคุณ

    for filename, veg_name in FILE_MAP.items():
        crop = Crop.objects.filter(crop_name=veg_name).first()
        if not crop:
            results.append({'file': filename, 'vegetable': veg_name, 'status': 'crop not found'})
            continue

        # กำหนด path ตามจริง
        # ถ้า filename มี folder ใน key อยู่แล้ว (เช่น "crop_images/xxx") ให้ใช้ตรงๆ
        # ถ้าไม่มี ให้มองใน media/crop_images/
        if '/' in filename or '\\' in filename:
            rel_path = filename.replace('\\', '/')
        else:
            rel_path = f"crop_images/{filename}"

        local_path = os.path.join(media_root, *rel_path.split('/'))

        if os.path.exists(local_path):
            with open(local_path, 'rb') as f:
                crop.crop_image.save(os.path.basename(filename), File(f), save=True)
            results.append({'file': filename, 'vegetable': veg_name, 'status': 'migrated'})
        else:
            results.append({'file': filename, 'vegetable': veg_name, 'status': 'file not found'})

    return Response(results)

@api_view(['GET'])
def debug_storage(request):
    """
    คืนชื่อ storage backend ที่กำลังใช้งานจริง
    """
    return Response({
        'default_storage': default_storage.__class__.__name__
    })