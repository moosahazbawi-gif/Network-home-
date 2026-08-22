# CloudBell Pro

خدمة تنزيلات آمنة مبنية على FastAPI و PostgreSQL و Redis و Celery، مع واجهة عربية ثابتة تعمل مباشرة عبر Nginx.

## المكونات

- API: FastAPI
- قاعدة البيانات: PostgreSQL 16
- عامل المهام: Celery
- وسيط الرسائل: Redis 7
- الواجهة: ملفات ثابتة بدون build
- الحماية من SSRF: تحقق DNS، منع الوجهات غير العامة، وتتبع كل تحويلة على حدة

## التشغيل السريع

1. انسخ المشروع إلى خادمك.
2. شغّل `./install.sh` لإنشاء ملف `.env` إذا لم يكن موجودا.
3. عدل القيم السرية، خصوصا:
   - `BOOTSTRAP_ADMIN_EMAIL`
   - `BOOTSTRAP_ADMIN_PASSWORD`
4. شغّل الحاويات:

```bash
docker compose up -d --build
```

5. افتح المتصفح على:

```text
http://localhost:8088
```

## التهيئة الأولى

لا يوجد تسجيل عام للمستخدمين. لإنشاء أول مسؤول، استخدم زر التهيئة في الواجهة أو استدعِ:

```http
POST /api/auth/bootstrap-admin
```

ويجب أن يطابق البريد وكلمة المرور القيم الموجودة في البيئة.

## النهاية البرمجية

- `GET /api/health`
- `POST /api/auth/bootstrap-admin`
- `POST /api/auth/login`
- `GET /api/auth/me`
- `POST /api/transfers`
- `GET /api/transfers`
- `GET /api/transfers/{id}`
- `POST /api/transfers/{id}/cancel`
- `GET /api/transfers/{id}/file`

## ملاحظات أمنية

- التنزيلات تمر عبر عامل Celery، وليس عبر الطلب المباشر.
- كل عنوان URL يمر بفحص المخطط والنطاق ونتائج DNS قبل التنفيذ.
- التحويلات تعاد فحصها في كل خطوة تحويل.
- الملفات لا تعرض إلا لمالكها المصادق عليه.

## فحص محلي

```bash
./validate.sh
```

هذا الفحص يتحقق من صحة بايثون وتركيب Docker Compose، لكنه لا يشغل Docker.
