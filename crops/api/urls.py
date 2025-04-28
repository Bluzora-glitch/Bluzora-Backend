from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views_api import (
    CropViewSet, 
    CropVariableViewSet, 
    PredictedDataViewSet,
    crops_list, 
    combined_price_forecast
)
from .export_excel import export_price_data_excel
from .crop_info_list import all_vegetable_info  # Import view จาก crop_info_list.py
from django.conf import settings
from django.conf.urls.static import static
from .quarterly_avg_api import quarterly_avg_data
from crops.api.views_api import migrate_images
from .views_api import debug_storage

router = DefaultRouter()
router.register(r'crops', CropViewSet)
router.register(r'crop-variables', CropVariableViewSet)
router.register(r'predicted-data', PredictedDataViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # URL สำหรับดึงรายชื่อผัก (แบบ crops_list)
    path('api/crops-list/', crops_list, name='crops_list'),
    # URL สำหรับ combined price forecast endpoint
    path('api/combined-priceforecast/', combined_price_forecast, name='combined_price_forecast'),
    # URL สำหรับ export excel endpoint
    path('api/export-excel/', export_price_data_excel, name='export_excel'),
    # URL สำหรับแสดงข้อมูลผักทั้งหมด (จาก Crop) ในรูปแบบที่ต้องการ
    path('api/crop-info-list/', all_vegetable_info, name='crop_info_list'),
    path('api/quarterly-avg/', quarterly_avg_data, name='quarterly_avg'),
    path('api/migrate-images/', migrate_images, name='migrate_images'),
    path('debug-storage/', debug_storage, name='debug_storage'),
]

if settings.DEBUG:  # ถ้าใน local development
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
