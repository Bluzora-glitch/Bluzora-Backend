from django.urls import path
from .views_data import update_crop_prices_from_request, update_all_crop_prices, home
from .views_ml import forecast_and_save
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('update-prices/', update_crop_prices_from_request, name='update-prices'),
    path('update-all-prices/', update_all_crop_prices, name='update_all_crop_prices'),
    path('forecast/', forecast_and_save, name='forecast_and_save'),
    path('', home, name='home'),  # เพิ่มเส้นทางให้แสดงหน้า home
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)