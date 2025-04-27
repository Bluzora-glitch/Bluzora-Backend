from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from crops.models import Crop, CropVariable, PredictedData  # เพิ่ม PredictedData
from django.utils.dateparse import parse_date
from rest_framework.renderers import JSONRenderer
import json
from datetime import datetime

# Custom JSON renderer ที่ใช้ ensure_ascii=False
class CustomJSONRenderer(JSONRenderer):
    charset = 'utf-8'
    def render(self, data, accepted_media_type=None, renderer_context=None):
        if data is None:
            return bytes()
        ret = json.dumps(data, ensure_ascii=False)
        return ret.encode(self.charset)

@api_view(['GET'])
@renderer_classes([CustomJSONRenderer])
def quarterly_avg_data(request):
    """
    รับ query parameters:
      - crop_name: ชื่อผักที่ต้องการค้นหา
      - startDate: วันที่เริ่มต้น (รูปแบบ YYYY-MM-DD)
      - endDate: วันที่สิ้นสุด (รูปแบบ YYYY-MM-DD)
    
    ส่งกลับข้อมูลในรูปแบบ JSON ดังนี้:
      {
        "name": <crop_name>,
        "unit": <unit>,
        "dailyPrices": [
            { "date": "2023-01-01", "min_price": 10, "max_price": 20, "average_price": 15 },
            { "date": "2023-01-02", "min_price": 11, "max_price": 21, "average_price": 16 },
            ...
        ],
        "predictedPrices": [
            { "date": "2023-01-03", "predicted_price": 17 },
            { "date": "2023-01-04", "predicted_price": 18 },
            ...
        ],
        "summary": {
            "overall_average": 15.5,
            "overall_min": 10,
            "overall_max": 21,
            "price_change": "⭣ 10% จาก 10 วันที่แล้ว"
        }
      }
    """
    crop_name = request.GET.get('crop_name')
    start_date_str = request.GET.get('startDate')
    end_date_str = request.GET.get('endDate')
    
    if not (crop_name and start_date_str and end_date_str):
        return Response({"error": "Missing required parameters"}, status=400)
    
    try:
        start_date = parse_date(start_date_str)
        if start_date is None:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = parse_date(end_date_str)
        if end_date is None:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
    except Exception as e:
        return Response({"error": "Invalid date format. Use YYYY-MM-DD."}, status=400)
    
    crop_obj = Crop.objects.filter(crop_name__icontains=crop_name.strip()).first()
    if not crop_obj:
        return Response({"error": "Crop not found"}, status=404)
    
    historical_qs = CropVariable.objects.filter(
        crop=crop_obj,
        date__gte=start_date,
        date__lte=end_date
    ).order_by('date')
    
    dailyPrices = []
    for var in historical_qs:
        dailyPrices.append({
            "date": var.date.isoformat(),
            "min_price": float(var.min_price) if var.min_price is not None else None,
            "max_price": float(var.max_price) if var.max_price is not None else None,
            "average_price": float(var.average_price) if var.average_price is not None else None,
        })
    
    # Query ข้อมูล predicted จาก PredictedData model
    predicted_qs = PredictedData.objects.filter(
        crop=crop_obj,
        predicted_date__gte=start_date,
        predicted_date__lte=end_date
    ).order_by('predicted_date')
    
    predictedPrices = []
    for item in predicted_qs:
        predictedPrices.append({
            "date": item.predicted_date.isoformat(),
            "predicted_price": float(item.predicted_price) if item.predicted_price is not None else None,
        })
    
    # คำนวณ summary
    avg_prices = [float(var.average_price) for var in historical_qs if var.average_price is not None]
    overall_average = sum(avg_prices) / len(avg_prices) if avg_prices else None

    min_prices = [float(var.min_price) for var in historical_qs if var.min_price is not None]
    overall_min = min(min_prices) if min_prices else None

    max_prices = [float(var.max_price) for var in historical_qs if var.max_price is not None]
    overall_max = max(max_prices) if max_prices else None

    if historical_qs.exists():
        start_var = historical_qs.first()
        end_var = historical_qs.last()
        if start_var and end_var and start_var.average_price:
            try:
                start_price = float(start_var.average_price)
                end_price = float(end_var.average_price)
                change_value = ((end_price - start_price) / start_price) * 100
                change_percent = round(abs(change_value), 2)
                days_diff = (end_date - start_date).days
                arrow = "⭡" if change_value >= 0 else "⭣"
                price_change_str = f"{arrow} {change_percent}% จาก {days_diff} วันที่แล้ว"
            except Exception as e:
                price_change_str = "-"
        else:
            price_change_str = "-"
    else:
        overall_average = None
        overall_min = None
        overall_max = None
        price_change_str = "-"
    
    summary = {
        "overall_average": overall_average,
        "overall_min": overall_min,
        "overall_max": overall_max,
        "price_change": price_change_str,
    }
    
    data = {
        "name": crop_obj.crop_name,
        "unit": crop_obj.unit,
        "dailyPrices": dailyPrices,
        "predictedPrices": predictedPrices,
        "summary": summary,
    }
    
    return Response(data)
