from django.urls import path
from .views_data import update_crop_prices_from_request, update_all_crop_prices
from .views_ml import forecast_and_save

urlpatterns = [
    path('update-prices/', update_crop_prices_from_request, name='update-prices'),
    path('update-all-prices/', update_all_crop_prices, name='update_all_crop_prices'),
    path('forecast/', forecast_and_save, name='forecast_and_save'),
]
