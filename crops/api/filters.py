import django_filters
from crops.models import Crop, CropVariable, PredictedData

class CropVariableFilter(django_filters.FilterSet):
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all(),
        label="Crop Name"
    )

    class Meta:
        model = CropVariable
        fields = ['crop']

class PredictedDataFilter(django_filters.FilterSet):
    crop = django_filters.ModelChoiceFilter(
        queryset=Crop.objects.all(),
        label="Crop Name"
    )

    class Meta:
        model = PredictedData
        fields = ['crop']
