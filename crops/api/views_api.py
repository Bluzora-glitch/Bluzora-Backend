from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.pagination import PageNumberPagination
from django.utils.dateparse import parse_date
from django.db.models import F
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
def combined_price_forecast(request):
    # รับ query parameter
    vegetable_name = request.GET.get('vegetableName')
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')
    
    # Debug prints
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
    historical_qs = CropVariable.objects.filter(
        crop=crop_obj,
        date__gte=start_date,
        date__lte=end_date
    ).values('date', 'average_price')
    
    # Query predicted data จาก PredictedData
    predicted_qs = PredictedData.objects.filter(
        crop=crop_obj,
        predicted_date__gte=start_date,
        predicted_date__lte=end_date
    ).values('predicted_date', 'predicted_price')
    
    # แปลงผลลัพธ์เป็น list ของ dictionary พร้อมเพิ่ม key "type"
    historical = [
        {
            "crop_name": crop_name,
            "date": str(item['date']),
            "price": float(item['average_price']),
            "type": "historical"
        }
        for item in historical_qs
    ]
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
    # เรียงลำดับโดยใช้ tuple (date, type_order)
    # โดยกำหนดให้ "historical" มีค่า order 0 และ "predicted" มีค่า order 1
    combined.sort(key=lambda x: (x['date'], 0 if x['type'] == "historical" else 1))
    
    return Response({"results": combined})
