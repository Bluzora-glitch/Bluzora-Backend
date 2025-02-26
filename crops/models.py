from django.db import models
from datetime import date


# 1. Crop Table
class Crop(models.Model):
    crop_name = models.CharField(max_length=255, unique=True)
    crop_image = models.ImageField(upload_to='crop_images/', null=True, blank=True)
    unit = models.CharField(max_length=50)
    grow_duration = models.IntegerField(help_text="ระยะเวลาปลูก (วัน)")

    def __str__(self):
        return self.crop_name

# 2. Crop_Variable Table
class CropVariable(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=date.today)  # ✅ ใช้ date.today() แทน datetime.today()
    file_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.crop.crop_name} - {self.date}"

# 3. Predicted_Data Table
class PredictedData(models.Model):
    crop = models.ForeignKey(Crop, on_delete=models.CASCADE)
    predicted_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.crop.crop_name} - {self.predicted_date}"
