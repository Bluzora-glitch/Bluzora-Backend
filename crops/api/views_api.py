from rest_framework import viewsets
from crops.models import Crop, CropVariable, PredictedData
from .serializers import CropSerializer, CropVariableSerializer, PredictedDataSerializer

class CropViewSet(viewsets.ModelViewSet):
    queryset = Crop.objects.all()
    serializer_class = CropSerializer
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น

class CropVariableViewSet(viewsets.ModelViewSet):
    queryset = CropVariable.objects.all()
    serializer_class = CropVariableSerializer
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น

class PredictedDataViewSet(viewsets.ModelViewSet):
    queryset = PredictedData.objects.all()
    serializer_class = PredictedDataSerializer
    http_method_names = ['get']  # กำหนดให้รองรับเฉพาะ GET เท่านั้น
