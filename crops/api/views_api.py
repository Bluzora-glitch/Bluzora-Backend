from rest_framework import viewsets
from .filters import CropVariableFilter, PredictedDataFilter
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from crops.models import Crop, CropVariable, PredictedData
from .serializers import CropSerializer, CropVariableSerializer, PredictedDataSerializer

class CropVariablePagination(PageNumberPagination):
    page_size = 100  # หรือกำหนดตามที่ต้องการ

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น

class CropVariableViewSet(viewsets.ModelViewSet):
    queryset = CropVariable.objects.all()
    serializer_class = CropVariableSerializer
    pagination_class = CropVariablePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = CropVariableFilter
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น

class PredictedDataViewSet(viewsets.ModelViewSet):
    queryset = PredictedData.objects.all()
    serializer_class = PredictedDataSerializer
    pagination_class = CropVariablePagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = PredictedDataFilter
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น
