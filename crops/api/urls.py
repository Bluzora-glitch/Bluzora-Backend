from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import CropViewSet, CropVariableViewSet, PredictedDataViewSet

router = DefaultRouter()
router.register(r'crops', CropViewSet)
router.register(r'crop-variables', CropVariableViewSet)
router.register(r'predicted-data', PredictedDataViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
]
