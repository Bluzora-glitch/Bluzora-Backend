from django.urls import path
from .views_data import update_crop_prices_from_request, update_all_crop_prices
from .views_ml import forecast_and_save
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Update prices
    path('update-prices/', update_crop_prices_from_request, name='update-prices'),
    path('update-all-prices/', update_all_crop_prices, name='update_all_crop_prices'),
    
    # Forecast
    path('forecast/', forecast_and_save, name='forecast_and_save'),
]

# Serve static files in development only
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
