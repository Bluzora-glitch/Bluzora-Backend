PostgreSQL password for the database superuser Honeyyy port 5432

mail: Bluzora System ,birth 16/02/2000
เมลgoogleงานนี้
bluzorasystem@gmail.com
Bluzorarara18
 superuser username: postgres
Email address: bluzorasystem@gmail.com
password: password


เซ็ท env ไว้ละ เปิดมาใช้
pip install -r requirements.txt

ถ้ายังไม่ได้
pip install django selenium pandas beautifulsoup4 requests

ใช้เพื่ออัพเดต database
python manage.py showmigrations
python manage.py migrate  # ถ้าพบว่าต้อง migrate

ใช้ runserver เพื่อดูหน้าเว็บ
python manage.py runserver


random forest https://colab.research.google.com/drive/1VmDUHsPRwsDxdIFXStAQHBdXFFD9AzQn?usp=sharing


เว็บเรียกใช้เพื่ออัพเดตพืชเข้า database
http://127.0.0.1:8000/api/update-all-prices/
เว็บ admin จัดการข้อมูล
http://127.0.0.1:8000/admin/crops/cropvariable/
ดูว่ามี url ไรบ้าง
python manage.py show_urls

อันนี้ ลืม
python manage.py shell
>>> from crops.models import CropVariable
>>> CropVariable.objects.all().delete()

เรียกใช้ postgresql
psql -U postgres
password ก็คือ password

ข้างล่างนี่ไม่มีไร

 crop           | table    | postgres
crop
crop_variable
predicted_data 



DROP TABLE IF EXISTS public.crop CASCADE;
DROP TABLE IF EXISTS public.crop_variable CASCADE;
DROP TABLE IF EXISTS public.predicted_data CASCADE;


crop_db=# \dt
                   List of relations
 Schema |            Name            | Type  |  Owner   
--------+----------------------------+-------+----------
 public | auth_group                 | table | postgres
 public | auth_group_permissions     | table | postgres
 public | auth_permission            | table | postgres
 public | auth_user                  | table | postgres
 public | auth_user_groups           | table | postgres
 public | auth_user_user_permissions | table | postgres
 public | crops_crop                 | table | postgres
 public | crops_cropvariable         | table | postgres
 public | crops_predicteddata        | table | postgres
 public | django_admin_log           | table | postgres
 public | django_content_type        | table | postgres
 public | django_migrations          | table | postgres
 public | django_session             | table | postgres
(13 rows)
