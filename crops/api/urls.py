from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import CropViewSet, CropVariableViewSet, PredictedDataViewSet
from .views_api import crops_list, combined_price_forecast  # import ฟังก์ชันใหม่ที่คุณสร้าง

router = DefaultRouter()
router.register(r'crops', CropViewSet)
router.register(r'crop-variables', CropVariableViewSet)
router.register(r'predicted-data', PredictedDataViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # เพิ่ม URL สำหรับ combined price forecast endpoint
    path('api/crops-list/', crops_list, name='crops_list'),
    path('api/combined-priceforecast/', combined_price_forecast, name='combined_price_forecast'),
]
