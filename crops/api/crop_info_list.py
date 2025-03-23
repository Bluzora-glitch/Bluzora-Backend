from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from crops.models import Crop, CropVariable
from django.utils.dateparse import parse_date
from rest_framework.renderers import JSONRenderer
import json
import urllib.parse

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
def all_vegetable_info(request):
    """
    ส่งกลับข้อมูลของผักทุกชนิดในตาราง Crops พร้อมกับข้อมูลจาก CropVariable
    รูปแบบที่ส่งกลับ:
      - name: ชื่อผัก (จาก Crop.crop_name) (จะไม่ encode เป็น percent-encoded)
      - unit: หน่วย (จาก Crop.unit)
      - price: "฿min - ฿max / unit" (จาก CropVariable ของวันที่ล่าสุด โดยไม่มีทศนิยม)
      - change: เปอร์เซ็นต์การเปลี่ยนแปลงราคา (คำนวณจาก historical data ของวันที่ล่าสุด)
      - image: URL รูปภาพแบบ absolute (จาก Crop.crop_image) โดยไม่ encode ชื่อไฟล์
      - status: "up" หรือ "down" ตามการเปลี่ยนแปลงราคา
    """
    crops = Crop.objects.all()
    result = []
    for crop in crops:
        historical_vars = CropVariable.objects.filter(crop=crop).order_by('date')
        if historical_vars.exists():
            latest = historical_vars.last()
            previous = historical_vars.exclude(date=latest.date).last()
            price_str = f"฿{int(latest.min_price)} - ฿{int(latest.max_price)} / {crop.unit}"
            if previous and previous.average_price:
                change_value = (latest.average_price - previous.average_price) / previous.average_price * 100
                change_percent = round(change_value, 2)
                if change_value >= 0:
                    change_str = f"↑ {change_percent}%"
                    status = "up"
                else:
                    change_str = f"↓ {abs(change_percent)}%"
                    status = "down"
            else:
                change_str = "↑ 0%"
                status = "up"
        else:
            price_str = ""
            change_str = ""
            status = ""
        
        if crop.crop_image:
            # รับค่า URL ที่ได้จาก crop.crop_image.url
            raw_url = crop.crop_image.url
            # ถ้า raw_url มี "crop_images/crop_images/" ให้แทนที่ด้วย "/crop_images/"
            if raw_url.startswith('/crop_images/crop_images/'):
                raw_url = raw_url.replace('/crop_images/crop_images/', '/crop_images/', 1)
            image_url = request.build_absolute_uri(raw_url)
            image_url = urllib.parse.unquote(image_url)
        else:
            image_url = request.build_absolute_uri("/assets/default.jpg")

        
        data = {
            "name": crop.crop_name,
            "unit": crop.unit,
            "price": price_str,
            "change": change_str,
            "image": image_url,
            "status": status,
        }
        result.append(data)
    
    return Response(result)
