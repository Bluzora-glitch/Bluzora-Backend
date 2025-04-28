from rest_framework.decorators import api_view, renderer_classes
from rest_framework.response import Response
from rest_framework.renderers import JSONRenderer
from django.utils.dateparse import parse_date
from crops.models import Crop, CropVariable
import json

# Custom JSON renderer ที่ใช้ ensure_ascii=False
defualt_charset = 'utf-8'
class CustomJSONRenderer(JSONRenderer):
    charset = defualt_charset
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
      - name: ชื่อผัก (จาก Crop.crop_name)
      - unit: หน่วย (จาก Crop.unit)
      - price: "฿min - ฿max / unit" (จาก CropVariable ของวันที่ล่าสุด)
      - avg_price: ราคาเฉลี่ย (จาก CropVariable ของวันที่ล่าสุด)
      - change: เปอร์เซ็นต์การเปลี่ยนแปลงราคา
      - image: URL รูปภาพเต็ม (จาก crop.crop_image.url)
      - status: "up" หรือ "down"
    """
    crops = Crop.objects.all()
    result = []

    for crop in crops:
        # ดึงข้อมูลราคาย้อนหลัง
        history = CropVariable.objects.filter(crop=crop).order_by('date')
        if history.exists():
            latest = history.last()
            previous = history.exclude(date=latest.date).last()

            price_str = f"฿{int(latest.min_price)} - ฿{int(latest.max_price)} / {crop.unit}"
            avg_price = f"฿{int(latest.average_price)} / {crop.unit}"

            if previous and previous.average_price:
                change_val = (latest.average_price - previous.average_price) / previous.average_price * 100
                change_pct = round(change_val, 2)
                if change_val >= 0:
                    change_str = f"↑ {change_pct}%"
                    status = "up"
                else:
                    change_str = f"↓ {abs(change_pct)}%"
                    status = "down"
            else:
                change_str = "↑ 0%"
                status = "up"
        else:
            price_str = avg_price = change_str = status = ""

        # จัดการ URL รูปภาพ (CloudinaryStorage จะคืน full URL)
        if crop.crop_image:
            image_url = crop.crop_image.url
        else:
            image_url = request.build_absolute_uri('/static/images/default.jpg')

        result.append({
            "name": crop.crop_name,
            "unit": crop.unit,
            "price": price_str,
            "avg_price": avg_price,
            "change": change_str,
            "image": image_url,
            "status": status,
        })

    return Response(result)
