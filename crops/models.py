from django.db import models
from datetime import date


# 1. Crop Table
class Crop(models.Model):
    crop_id = models.AutoField(primary_key=True)  # กำหนด PK ชื่อ crop_id
    crop_image = models.ImageField(upload_to='crop_images/', null=True, blank=True)
    crop_name = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=50)
    grow_duration = models.IntegerField(help_text="ระยะเวลาปลูก (วัน)")

    def __str__(self):
        return self.crop_name


# 2. Crop_Variable Table
class CropVariable(models.Model):
    variable_id = models.AutoField(primary_key=True)  # ถ้าอยากให้มี PK ชื่อ variable_id
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        db_column='crop_id'  # บอก Django ว่าใช้คอลัมน์ชื่อ crop_id เป็น FK
    )
    average_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField()
    file_name = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.crop.crop_name} - {self.date}"

# 3. Predicted_Data Table
class PredictedData(models.Model):
    # สมมติให้มี PK ชื่อ predicted_id หรือจะใช้คอลัมน์อื่นก็ได้
    predicted_id = models.AutoField(primary_key=True)
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        db_column='crop_id'
    )
    predicted_date = models.DateField()
    predicted_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.crop.crop_name} - {self.predicted_date}"