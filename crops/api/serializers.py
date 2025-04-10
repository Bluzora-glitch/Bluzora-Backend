from rest_framework import serializers
from crops.models import Crop, CropVariable, PredictedData

class CropSerializer(serializers.ModelSerializer):
    class Meta:
        model = Crop
        fields = '__all__'

class CropVariableSerializer(serializers.ModelSerializer):
    crop = serializers.StringRelatedField()  # หรือสามารถใช้ nested serializer
    class Meta:
        model = CropVariable
        fields = '__all__'

class PredictedDataSerializer(serializers.ModelSerializer):
    crop = serializers.StringRelatedField()
    class Meta:
        model = PredictedData
        fields = '__all__'
