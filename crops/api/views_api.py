from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_date
from django.db.models import F
from django.http import JsonResponse
from crops.models import Crop, CropVariable, PredictedData
from .filters import CropVariableFilter, PredictedDataFilter
from .serializers import CropSerializer, CropVariableSerializer, PredictedDataSerializer
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
    
    return Response({
        "results": combined,
        "combined": combined_price_list,
        "overall_summary": overall_summary
    })

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
