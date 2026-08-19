Must set 8000 as port in geenral settings in coolify


Use this for enviromnent variable:
-----------------------------------------------------
SECRET_KEY=(s&-x6got5(=ia%nqrzp9fe74#z@wajklh9s$mdp(+!)w^5qwq
DEBUG=False

ALLOWED_HOSTS=orderapi.englishcommando.bd
CSRF_TRUSTED_ORIGINS=https://orderapi.englishcommando.bd
CORS_ALLOWED_ORIGINS=https://oxfordvocab.englishcommando.bd

TIME_ZONE=Asia/Dhaka
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

USE_REDIS=False
CELERY_TASK_ALWAYS_EAGER=True

DATABASE_URL=mysql://mysql:M5QIODb3Ix2YVFupmqIvPCMsKA8SmxQelR3zgL1U8m8xctmGvBeMsnwHvrG6bx2R@ve6txhct3rnce8onl8lptxlc:3306/db

DB_ENGINE=django.db.backends.mysql
DB_NAME=db
DB_USER=mysql
DB_PASSWORD=M5QIODb3Ix2YVFupmqIvPCMsKA8SmxQelR3zgL1U8m8xctmGvBeMsnwHvrG6bx2R
DB_HOST=localhost
DB_PORT=3315

REDIS_URL=redis://redis-service:6379/0
CELERY_BROKER_URL=redis://redis-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-service:6379/1

STEADFAST_API_BASE_URL=https://portal.packzy.com/api/v1
STEADFAST_API_KEY=your_api_key
STEADFAST_SECRET_KEY=your_secret_key



or
-----------------------------------

SECRET_KEY=(s&-x6got5(=ia%nqrzp9fe74#z@wajklh9s$mdp(+!)w^5qwq
DEBUG=False
ALLOWED_HOSTS=orderapi.englishcommando.bd
CSRF_TRUSTED_ORIGINS=https://orderapi.englishcommando.bd
CORS_ALLOWED_ORIGINS=https://oxfordvocab.englishcommando.bd
TIME_ZONE=Asia/Dhaka
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
USE_REDIS=False
CELERY_TASK_ALWAYS_EAGER=True
DATABASE_URL=mysql://mysql:M5QIODb3Ix2YVFupmqIvPCMsKA8SmxQelR3zgL1U8m8xctmGvBeMsnwHvrG6bx2R@ve6txhct3rnce8onl8lptxlc:3306/db
REDIS_URL=redis://redis-service:6379/0
CELERY_BROKER_URL=redis://redis-service:6379/0
CELERY_RESULT_BACKEND=redis://redis-service:6379/1
STEADFAST_API_BASE_URL=https://portal.packzy.com/api/v1
STEADFAST_API_KEY=your_api_key
STEADFAST_SECRET_KEY=your_secret_key