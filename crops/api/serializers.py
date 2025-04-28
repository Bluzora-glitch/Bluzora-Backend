from rest_framework import serializers
from crops.models import Crop, CropVariable, PredictedData

class CropSerializer(serializers.ModelSerializer):
    image_url = serializers.SerializerMethodField()
    class Meta:
        model = Crop
        fields = '__all__'
    def get_image_url(self, obj):
        return obj.crop_image.url if obj.crop_image else None

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
