from django.db import models
from datetime import date

# 1. Crop Table
class Crop(models.Model):
    crop_id = models.AutoField(primary_key=True)
    crop_image = models.ImageField(upload_to="", null=True, blank=True)
    crop_name = models.CharField(max_length=255, unique=True)
    unit = models.CharField(max_length=50)
    min_growth_duration = models.IntegerField(help_text="ระยะเวลาปลูกขั้นต่ำ (วัน)",default=30)
    max_growth_duration = models.IntegerField(help_text="ระยะเวลาปลูกสูงสุด (วัน)",default=60)
    ideal_soil = models.TextField(help_text="ข้อมูลดินที่เหมาะสม", blank=True, null=True)
    optimal_season = models.TextField(help_text="ฤดูกาลที่เหมาะสมในการปลูก", blank=True, null=True)
    cultivation_method = models.TextField(help_text="วิธีการเพาะปลูกและดูแลรักษา", blank=True, null=True)
    care_tips = models.TextField(help_text="เคล็ดลับการดูแลรักษา", blank=True, null=True)

    def __str__(self):
        return self.crop_name

    def get_growth_duration_display(self):
        """
        ฟังก์ชันสำหรับแสดงผลระยะเวลาการเติบโต
        ถ้าค่าทั้งสองเท่ากันจะแสดงเป็น "50 วัน" 
        แต่ถ้าไม่เท่ากัน จะแสดงเป็น "40-60 วัน"
        """
        if self.min_growth_duration == self.max_growth_duration:
            return f"{self.min_growth_duration} วัน"
        else:
            return f"{self.min_growth_duration}-{self.max_growth_duration} วัน"


# 2. Crop_Variable Table
class CropVariable(models.Model):
    variable_id = models.AutoField(primary_key=True)
    crop = models.ForeignKey(
        Crop,
        on_delete=models.CASCADE,
        db_column='crop_id'
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


# 4. Crop Model Mapping Table
class CropModelMapping(models.Model):
    mapping_id = models.AutoField(primary_key=True)
    # ใช้ความสัมพันธ์แบบ One-to-One เพื่อให้แน่ใจว่าแต่ละพืชมี mapping ไฟล์โมเดลเพียงรายการเดียว
    crop = models.OneToOneField(
        Crop,
        on_delete=models.CASCADE,
        related_name='model_mapping'
    )
    model_path = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.crop.crop_name} -> {self.model_path}"
