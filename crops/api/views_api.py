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
    data = serializer.data  # data เป็น List ของ dict ที่มี key เช่น 'crop_name'
    
    # สร้าง JsonResponse พร้อม ensure_ascii=False และกำหนด Content-Type ด้วย charset=utf-8
    response = JsonResponse(data, safe=False, json_dumps_params={'ensure_ascii': False})
    response['Content-Type'] = 'application/json; charset=utf-8'
    return response


@api_view(['GET'])
def combined_price_forecast(request):
    """
    Endpoint รวมข้อมูล Historical และ Predicted
    โดย Historical จะส่ง min_price, max_price, average_price
    และ Predicted จะส่ง predicted_price
    """
    # รับ query parameter
    vegetable_name = request.GET.get('vegetableName')
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')
    
    print("Received vegetableName:", vegetable_name)
    print("Received startDate:", start_date_str)
    print("Received endDate:", end_date_str)
    
    if not (vegetable_name and start_date_str and end_date_str):
        return Response({"error": "Missing parameters"}, status=400)
    
    # แปลงวันที่
    start_date = parse_date(start_date_str)
    end_date = parse_date(end_date_str)
    if not (start_date and end_date):
        return Response({"error": "Invalid date format"}, status=400)
    
    # ทำความสะอาดค่า vegetableName
    vegetable_name_clean = vegetable_name.strip()
    print("Clean vegetableName:", vegetable_name_clean)
    
    # ค้นหา Crop โดยใช้ __icontains
    crop_obj = Crop.objects.filter(crop_name__icontains=vegetable_name_clean).first()
    print("Matched Crop:", crop_obj)
    if not crop_obj:
        return Response({"error": "Crop not found"}, status=404)
    
    crop_name = crop_obj.crop_name
    
    # Query historical data จาก CropVariable
    # เพิ่มการดึง min_price, max_price ด้วย
    historical_qs = CropVariable.objects.filter(
        crop=crop_obj,
        date__gte=start_date,
        date__lte=end_date
    ).values(
        'date',
        'average_price',
        'min_price',
        'max_price',
    )
    
    # Query predicted data จาก PredictedData
    predicted_qs = PredictedData.objects.filter(
        crop=crop_obj,
        predicted_date__gte=start_date,
        predicted_date__lte=end_date
    ).values('predicted_date', 'predicted_price')
    
    # สร้าง list ของ dictionary สำหรับ Historical
    historical = [
        {
            "crop_name": crop_name,
            "date": str(item['date']),
            "min_price": float(item['min_price']),     # ราคาต่ำสุด
            "max_price": float(item['max_price']),     # ราคาสูงสุด
            "price": float(item['average_price']),     # price เก็บค่า average_price (ถ้า front-end ยังใช้ key 'price')
            "type": "historical"
        }
        for item in historical_qs
    ]
    
    # สร้าง list ของ dictionary สำหรับ Predicted
    predicted = [
        {
            "crop_name": crop_name,
            "date": str(item['predicted_date']),
            "price": float(item['predicted_price']),
            "type": "predicted"
        }
        for item in predicted_qs
    ]
    
    # รวมข้อมูลทั้งสองชุด
    combined = historical + predicted
    
    # เรียงลำดับโดยวันที่ + ให้ historical มาก่อนถ้าวันเดียวกัน
    combined.sort(key=lambda x: (x['date'], 0 if x['type'] == "historical" else 1))
    
    return Response({"results": combined})
