# InvestCalc DSS — Serverga o'rnatish (Deploy) qo'llanmasi

Ushbu hujjat **InvestCalc DSS** (Django 5 + PostgreSQL) loyihasini productiondagi serverga joylashtirish bo'yicha to'liq yo'riqnomadir. 3 xil variant bor — o'zingizga qulayini tanlang.

- [Tez variantlar: qaysi birini tanlash kerak?](#tez-variantlar-qaysi-birini-tanlash-kerak)
- [1-variant: Ubuntu VPS (Nginx + Gunicorn + PostgreSQL)](#1-variant-ubuntu-vps-nginx--gunicorn--postgresql) — **tavsiya etiladi**
- [2-variant: Docker Compose](#2-variant-docker-compose)
- [3-variant: Render / Railway (bir marta bosish)](#3-variant-render--railway)
- [Umumiy: `.env` shabloni](#umumiy-env-shabloni)
- [Xavfsizlik checklist](#xavfsizlik-checklist)
- [Keyingi servis (Monitoring, Backup)](#keyingi-servis-monitoring-backup)

---

## Tez variantlar: qaysi birini tanlash kerak?

| Stsenariy | Tavsiya |
|-----------|---------|
| O'z VPS/VDS (2 GB RAM yetadi) va domen bor | **1-variant — Ubuntu + Nginx + Gunicorn** |
| Docker bilan tezda ko'tarmoqchiman, CI/CD ham keyin | **2-variant — Docker Compose** |
| Ko'p vaqt sarflashni xohlamayman, demo kerak | **3-variant — Render.com** |

---

## 1-variant: Ubuntu VPS (Nginx + Gunicorn + PostgreSQL)

> **Talablar:** Ubuntu 22.04+ VPS (2 vCPU, 2 GB RAM, 20 GB SSD), `root` yoki `sudo` huquqi, domen (masalan, `investcalc.uz`) va DNS A-yozuvi serverning IP-siga ishora qiladi.

### 1.1. Server paketlarini o'rnatish

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.12 python3.12-venv python3-pip \
    postgresql postgresql-contrib \
    nginx git certbot python3-certbot-nginx \
    build-essential libpq-dev
```

### 1.2. PostgreSQL foydalanuvchisi va DB

```bash
sudo -u postgres psql <<'SQL'
CREATE DATABASE investcalc;
CREATE USER investcalc WITH ENCRYPTED PASSWORD 'STRONG_PASSWORD_HERE';
ALTER ROLE investcalc SET client_encoding TO 'utf8';
ALTER ROLE investcalc SET default_transaction_isolation TO 'read committed';
ALTER ROLE investcalc SET timezone TO 'Asia/Tashkent';
GRANT ALL PRIVILEGES ON DATABASE investcalc TO investcalc;
\c investcalc
GRANT ALL ON SCHEMA public TO investcalc;
SQL
```

### 1.3. Ilova foydalanuvchisi va kod

```bash
sudo adduser --system --group --home /opt/investcalc investcalc
sudo mkdir -p /opt/investcalc
sudo chown investcalc:investcalc /opt/investcalc

sudo -u investcalc git clone <REPO-URL> /opt/investcalc/app
cd /opt/investcalc/app

sudo -u investcalc python3.12 -m venv /opt/investcalc/venv
sudo -u investcalc /opt/investcalc/venv/bin/pip install --upgrade pip
sudo -u investcalc /opt/investcalc/venv/bin/pip install -r requirements.txt
sudo -u investcalc /opt/investcalc/venv/bin/pip install gunicorn whitenoise
```

> Agar `git clone` o'rniga arxiv ishlatsangiz: `scp -r ./InvestCalculator root@SERVER:/opt/investcalc/app` va `sudo chown -R investcalc:investcalc /opt/investcalc/app`.

### 1.4. `.env` fayli

`/opt/investcalc/app/.env`:

```ini
DEBUG=False
SECRET_KEY=<python -c "import secrets; print(secrets.token_urlsafe(64))" natijasi>
ALLOWED_HOSTS=investcalc.uz,www.investcalc.uz

USE_SQLITE=False
POSTGRES_DB=investcalc
POSTGRES_USER=investcalc
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
```

```bash
sudo chmod 600 /opt/investcalc/app/.env
sudo chown investcalc:investcalc /opt/investcalc/app/.env
```

### 1.5. Whitenoise (static fayllar uchun)

`investcalc/settings.py` faylida ikki joyga o'zgartirish kiriting (agar hozircha yo'q bo'lsa):

```python
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    ...
]

STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"
```

### 1.6. DB migratsiya va static to'plash

```bash
cd /opt/investcalc/app
sudo -u investcalc /opt/investcalc/venv/bin/python manage.py migrate
sudo -u investcalc /opt/investcalc/venv/bin/python manage.py collectstatic --noinput
sudo -u investcalc /opt/investcalc/venv/bin/python manage.py createsuperuser
```

### 1.7. Gunicorn `systemd` servis

`/etc/systemd/system/investcalc.service`:

```ini
[Unit]
Description=InvestCalc Gunicorn
After=network.target postgresql.service

[Service]
User=investcalc
Group=investcalc
WorkingDirectory=/opt/investcalc/app
EnvironmentFile=/opt/investcalc/app/.env
ExecStart=/opt/investcalc/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/run/investcalc.sock \
    --access-logfile /var/log/investcalc/access.log \
    --error-logfile /var/log/investcalc/error.log \
    --timeout 60 \
    investcalc.wsgi:application
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo mkdir -p /var/log/investcalc
sudo chown investcalc:investcalc /var/log/investcalc

sudo systemctl daemon-reload
sudo systemctl enable --now investcalc
sudo systemctl status investcalc
```

### 1.8. Nginx reverse proxy

`/etc/nginx/sites-available/investcalc`:

```nginx
server {
    listen 80;
    server_name investcalc.uz www.investcalc.uz;

    client_max_body_size 10m;

    location /static/ {
        alias /opt/investcalc/app/staticfiles/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://unix:/run/investcalc.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/investcalc /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 1.9. HTTPS (Let's Encrypt)

```bash
sudo certbot --nginx -d investcalc.uz -d www.investcalc.uz
sudo systemctl enable certbot.timer
```

`settings.py` ga production uchun quyidagilarni qo'shing (HTTPS yoqilgandan keyin):

```python
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    CSRF_TRUSTED_ORIGINS = ["https://investcalc.uz", "https://www.investcalc.uz"]
```

### 1.10. Tekshirish

```bash
curl -I https://investcalc.uz
# Kutilayotgan javob: HTTP/2 200, server: nginx
```

Brauzerda `https://investcalc.uz/` ga kiring — Hero sahifasi ochilishi kerak.

### 1.11. Yangilanishni chiqarish (deploy)

```bash
cd /opt/investcalc/app
sudo -u investcalc git pull
sudo -u investcalc /opt/investcalc/venv/bin/pip install -r requirements.txt
sudo -u investcalc /opt/investcalc/venv/bin/python manage.py migrate
sudo -u investcalc /opt/investcalc/venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart investcalc
```

---

## 2-variant: Docker Compose

> Tavsiya: Docker va Docker Compose o'rnatilgan server (Ubuntu / Debian / macOS).

### 2.1. Fayllarni yaratish

Loyiha ildizida quyidagi 3 faylni qo'shing (shablonlari pastda).

**`Dockerfile`**

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install gunicorn whitenoise

COPY . .

RUN python manage.py collectstatic --noinput || true

EXPOSE 8000
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "3", "--timeout", "60", "investcalc.wsgi:application"]
```

**`.dockerignore`**

```
.git
.venv
__pycache__
*.pyc
db.sqlite3
staticfiles
.env
cookies.txt
*.log
```

**`docker-compose.yml`**

```yaml
services:
  db:
    image: postgres:16-alpine
    restart: unless-stopped
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - pg_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $$POSTGRES_USER"]
      interval: 10s
      retries: 5

  web:
    build: .
    restart: unless-stopped
    env_file: .env
    depends_on:
      db:
        condition: service_healthy
    volumes:
      - static_data:/app/staticfiles
    ports:
      - "8000:8000"
    command: >
      sh -c "python manage.py migrate &&
             python manage.py collectstatic --noinput &&
             gunicorn --bind 0.0.0.0:8000 --workers 3 --timeout 60 investcalc.wsgi:application"

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - static_data:/static:ro
    depends_on:
      - web

volumes:
  pg_data:
  static_data:
```

**`nginx.conf`**

```nginx
server {
    listen 80;
    server_name _;

    client_max_body_size 10m;

    location /static/ {
        alias /static/;
        expires 30d;
    }

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### 2.2. `.env` to'ldirish

[Umumiy: `.env` shabloni](#umumiy-env-shabloni) dagidek to'ldiring, qo'shimcha: `POSTGRES_HOST=db`.

### 2.3. Ishga tushirish

```bash
docker compose build
docker compose up -d
docker compose logs -f web
docker compose exec web python manage.py createsuperuser
```

Endi `http://SERVER-IP/` da ilova mavjud. HTTPS uchun **Caddy** ishlatish yoki yuqorida ko'rsatilgan Certbot usuli (host mashinada Nginx bilan) mos keladi.

### 2.4. Yangilanish

```bash
git pull
docker compose build web
docker compose up -d web
```

---

## 3-variant: Render / Railway

> Hech qanday VPS sozlamasiz, 5 daqiqada deploy.

### 3.1. Render.com

1. [render.com](https://render.com) ga kiring va GitHub repozitoriyni ulang.
2. **New → Blueprint** — loyiha ildiziga `render.yaml` qo'shib quyidagini yozing:

```yaml
services:
  - type: web
    name: investcalc
    env: python
    buildCommand: |
      pip install -r requirements.txt gunicorn whitenoise
      python manage.py collectstatic --noinput
      python manage.py migrate
    startCommand: gunicorn investcalc.wsgi:application --workers 3 --timeout 60
    envVars:
      - key: DEBUG
        value: "False"
      - key: SECRET_KEY
        generateValue: true
      - key: ALLOWED_HOSTS
        value: "investcalc.onrender.com"
      - key: USE_SQLITE
        value: "False"
      - fromDatabase:
          name: investcalc-db
          property: connectionString

databases:
  - name: investcalc-db
    plan: free
```

3. Render avtomatik `DATABASE_URL` ni beradi. Buni o'qish uchun `settings.py` ga qo'shing:

```python
import dj_database_url

if env("DATABASE_URL", default=None):
    DATABASES["default"] = dj_database_url.parse(env("DATABASE_URL"))
```

va `pip install dj-database-url` (requirements.txt ga `dj-database-url>=2.1` qo'shing).

### 3.2. Railway.app

Xuddi shunday — GitHub repo ni ulab, `Add PostgreSQL` bosing, environment variable'larni qo'shing. Build va start buyruqlari Render bilan bir xil.

---

## Umumiy: `.env` shabloni

Loyiha ildiziga `.env` yarating (git ga **qo'shmang**):

```ini
# --- Asosiy ---
DEBUG=False
SECRET_KEY=replace-me-with-64-char-random-string
ALLOWED_HOSTS=investcalc.uz,www.investcalc.uz

# --- Ma'lumotlar bazasi ---
USE_SQLITE=False
POSTGRES_DB=investcalc
POSTGRES_USER=investcalc
POSTGRES_PASSWORD=STRONG_PASSWORD_HERE
POSTGRES_HOST=127.0.0.1     # Docker da: db
POSTGRES_PORT=5432
```

`SECRET_KEY` yaratish:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## Xavfsizlik checklist

- [ ] `DEBUG=False` production `.env` da
- [ ] `SECRET_KEY` — noyob, 50+ belgi, repositoryda emas
- [ ] `ALLOWED_HOSTS` — aniq domenlar (yulduzcha yo'q)
- [ ] `.env` fayli `chmod 600` va `.gitignore` da
- [ ] PostgreSQL parol kuchli (16+ belgi)
- [ ] HTTPS yoqilgan (Let's Encrypt)
- [ ] `SECURE_SSL_REDIRECT = True`, `SESSION_COOKIE_SECURE = True`, `CSRF_COOKIE_SECURE = True`
- [ ] `HSTS` yoqilgan (birinchi marta qo'shganda 1 soatdan boshlang, keyin 1 yil)
- [ ] Admin URL'ni o'zgartirish (ixtiyoriy): `/admin/` → `/sys-panel-7g3/`
- [ ] Firewall: faqat 22, 80, 443 portlar ochiq (`ufw allow 'Nginx Full' && ufw allow OpenSSH`)
- [ ] Superuser uchun kuchli parol
- [ ] Sensitive xatolarni e-mail ga yuborish (`ADMINS` va SMTP sozlash)

---

## Keyingi servis: Monitoring, Backup

### DB backup (har kuni 03:00)

`/etc/cron.d/investcalc-backup`:

```cron
0 3 * * * investcalc pg_dump -U investcalc investcalc | gzip > /opt/investcalc/backups/db_$(date +\%Y\%m\%d).sql.gz
0 4 * * 0 root find /opt/investcalc/backups -name "*.sql.gz" -mtime +30 -delete
```

### Log aylantirish

`/etc/logrotate.d/investcalc`:

```
/var/log/investcalc/*.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
    create 0640 investcalc investcalc
    sharedscripts
    postrotate
        systemctl reload investcalc > /dev/null 2>&1 || true
    endscript
}
```

### Sog'liqni tekshirish (uptime)

- [UptimeRobot](https://uptimerobot.com/) — bepul, 5 daqiqalik interval.
- URL: `https://investcalc.uz/` — 200 javobni kutib turadi.

### Sentry (xatoliklarni kuzatish, ixtiyoriy)

```bash
pip install sentry-sdk
```

`settings.py`:

```python
if not DEBUG and env("SENTRY_DSN", default=None):
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration

    sentry_sdk.init(
        dsn=env("SENTRY_DSN"),
        integrations=[DjangoIntegration()],
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
```

---

## Yordam kerakmi?

- Django hujjatlari: <https://docs.djangoproject.com/en/5.0/howto/deployment/>
- Gunicorn: <https://docs.gunicorn.org/>
- xhtml2pdf (PDF ishlashi uchun muammo bo'lsa): <https://xhtml2pdf.readthedocs.io/>

**Muvaffaqiyatli deploy!** Agar xato yoki savol bo'lsa — issue oching.
