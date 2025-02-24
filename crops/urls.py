from django.urls import path
from .views import update_crop_prices_from_request, update_all_crop_prices

urlpatterns = [
    path('update-prices/', update_crop_prices_from_request, name='update-prices'),
    path('update-all-prices/', update_all_crop_prices, name='update_all_crop_prices'),
]
