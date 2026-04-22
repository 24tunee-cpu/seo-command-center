# SEO Cyber Command Center - Kurulum ve Deployment Rehberi

Bu rehber, SEO Command Center platformunun kurulumu, yapılandırılması ve ölçeklendirilmesi için adım adım talimatlar içermektedir.

## 📋 İçindekiler

1. [Sistem Gereksinimleri](#sistem-gereksinimleri)
2. [Mimari Özet](#mimari-özet)
3. [Hızlı Başlangıç](#hızlı-başlangıç)
4. [Geliştirme Ortamı Kurulumu](#geliştirme-ortamı-kurulumu)
5. [Production Deployment](#production-deployment)
6. [API Yapılandırması](#api-yapılandırması)
7. [Ölçeklendirme Stratejisi](#ölçeklendirme-stratejisi)
8. [Sorun Giderme](#sorun-giderme)

## Sistem Gereksinimleri

### Minimum Gereksinimler
- **CPU**: 4 çekirdek
- **RAM**: 8 GB
- **Disk**: 50 GB SSD
- **OS**: Ubuntu 20.04 LTS veya üzeri / Windows 10/11

### Önerilen Gereksinimler (Production)
- **CPU**: 8+ çekirdek
- **RAM**: 16 GB+
- **Disk**: 100 GB NVMe SSD
- **Network**: 1 Gbps

### Gerekli Yazılımlar
- Docker 24.0+
- Docker Compose 2.20+
- Python 3.11+ (geliştirme için)
- Node.js 20+ (geliştirme için)
- Git

## Mimari Özet

```
┌─────────────────────────────────────────────────────────────┐
│                     Kullanıcı (Browser)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTPS
┌─────────────────────▼───────────────────────────────────────┐
│                    Next.js Frontend                        │
│              (Port: 3000, Glassmorphism UI)                │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/JSON
┌─────────────────────▼───────────────────────────────────────┐
│                   FastAPI Backend                          │
│              (Port: 8000, Async Python)                    │
└──────────┬──────────────┬──────────────┬─────────────────┘
           │              │              │
┌──────────▼───┐  ┌───────▼─────┐  ┌─────▼──────┐
│   MongoDB     │  │    Redis    │  │   Celery   │
│  (Port:27017) │  │ (Port:6379) │  │  Workers   │
│  Time-series  │  │   Queue     │  │            │
└───────────────┘  └─────────────┘  └────────────┘
```

## Hızlı Başlangıç

### 1. Repoyu Klonlayın

```bash
git clone https://github.com/your-org/seo-command-center.git
cd seo-command-center
```

### 2. Environment Dosyalarını Oluşturun

```bash
# Backend için
cp backend/.env.example backend/.env

# Frontend için
echo "NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1" > frontend/.env.local
```

### 3. Docker ile Çalıştırın

```bash
# Tüm servisleri başlat
docker-compose up -d

# Logları izleyin
docker-compose logs -f
```

### 4. Erişim Noktaları

| Servis | URL | Açıklama |
|--------|-----|----------|
| Dashboard | http://localhost:3000 | Next.js Frontend |
| API Docs | http://localhost:8000/api/docs | Swagger UI |
| Flower | http://localhost:5555 | Celery Monitoring |
| MongoDB | localhost:27017 | Veritabanı |

## Geliştirme Ortamı Kurulumu

### Backend Kurulumu (Windows/Linux)

```bash
cd backend

# Virtual environment oluşturun
python -m venv venv

# Windows
cd venv\Scripts && activate && cd ..\..

# Linux/Mac
source venv/bin/activate

# Bağımlılıkları yükleyin
pip install -r requirements.txt

# MongoDB ve Redis'in çalıştığından emin olun
docker-compose up -d mongodb redis

# Uygulamayı çalıştırın
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Kurulumu

```bash
cd frontend

# Bağımlılıkları yükleyin
npm install

# Geliştirme sunucusunu başlatın
npm run dev
```

## Production Deployment

### 1. Cloud VPS Kurulumu (Örnek: AWS/DigitalOcean)

```bash
# Sunucuya bağlanın
ssh root@your-server-ip

# Docker kurulumu
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Docker Compose kurulumu
sudo curl -L "https://github.com/docker/compose/releases/download/v2.23.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. SSL/TLS Yapılandırması (Let's Encrypt)

```bash
# Nginx Reverse Proxy ile
sudo apt install nginx certbot python3-certbot-nginx

# Nginx yapılandırması
sudo nano /etc/nginx/sites-available/seo-command
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
    }
}
```

```bash
# Sertifika alın
sudo certbot --nginx -d your-domain.com

# Nginx'i yeniden başlatın
sudo systemctl restart nginx
```

### 3. Production Environment Variables

```bash
# backend/.env dosyanız şu şekilde olmalı:
DEBUG=false
SECRET_KEY=your-256-bit-secret-key-here
MONGODB_URI=mongodb://admin:secure-password@mongodb:27017/seo_command_center?authSource=admin
REDIS_URL=redis://redis:6379/0

# API Keys (Production)
PAGESPEED_API_KEY=your-google-api-key
SERPAPI_KEY=your-serpapi-key
GOOGLE_PLACES_API_KEY=your-places-api-key
```

### 4. Monitoring ve Logging

```bash
# Prometheus + Grafana kurulumu (opsiyonel)
docker-compose -f docker-compose.monitoring.yml up -d

# Log rotation yapılandırması
sudo nano /etc/logrotate.d/seo-command
```

```
/var/lib/docker/containers/*/*.log {
    rotate 7
    daily
    compress
    missingok
    delaycompress
    copytruncate
}
```

## API Yapılandırması

### Google PageSpeed Insights API

1. [Google Cloud Console](https://console.cloud.google.com/)'a gidin
2. Yeni proje oluşturun
3. PageSpeed Insights API'yi etkinleştirin
4. API Key oluşturun ve `.env`'e ekleyin

### SerpApi Yapılandırması

1. [SerpApi](https://serpapi.com/)'ye kaydolun
2. API Key alın
3. `.env` dosyasına ekleyin

### Google Places API

1. Google Cloud Console'da Places API'yi etkinleştirin
2. Billing hesabı ekleyin
3. API Key oluşturun

## Ölçeklendirme Stratejisi

### Yatay Ölçeklendirme (Horizontal Scaling)

```yaml
# docker-compose.override.yml
version: '3.8'
services:
  backend:
    deploy:
      replicas: 3
    environment:
      - WORKERS=4
      
  celery:
    deploy:
      replicas: 5
```

### MongoDB Sharding (Büyük Veri için)

```bash
# Config Server
docker run -d --name mongo-config \
  mongo:7.0 mongod --configsvr --replSet configRS

# Shard'lar
docker run -d --name mongo-shard1 \
  mongo:7.0 mongod --shardsvr --replSet shard1RS
```

### Redis Cluster

```yaml
services:
  redis-master:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    
  redis-replica:
    image: redis:7-alpine
    command: redis-server --slaveof redis-master 6379
```

### Load Balancer (Nginx)

```nginx
upstream backend {
    least_conn;
    server backend1:8000;
    server backend2:8000;
    server backend3:8000;
}

server {
    location /api/ {
        proxy_pass http://backend;
    }
}
```

## Sorun Giderme

### Sık Karşılaşılan Hatalar

#### 1. MongoDB Bağlantı Hatası

```
Error: Cannot connect to MongoDB
```

**Çözüm:**
```bash
# MongoDB konteyner'ının çalıştığını kontrol edin
docker-compose ps

# MongoDB loglarını kontrol edin
docker-compose logs mongodb

# Kimlik bilgilerini doğrulayın
docker exec -it seo-mongodb mongosh -u admin -p password --authenticationDatabase admin
```

#### 2. Redis Bağlantı Hatası

```
Error: Connection refused to Redis
```

**Çözüm:**
```bash
# Redis konteyner'ını yeniden başlatın
docker-compose restart redis

# Redis bağlantısını test edin
docker exec -it seo-redis redis-cli ping
```

#### 3. Memory Sorunları

```bash
# Bellek kullanımını kontrol edin
docker stats

# Swap alanı ekleyin
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Performans Optimizasyonu

#### MongoDB İndeks Optimizasyonu

```javascript
// MongoDB shell'de çalıştırın
db.crawl_audits.createIndex({ "project_id": 1, "crawled_at": -1 })
db.local_search_rankings.createIndex({ "project_id": 1, "keyword": 1 })
```

#### Backend Cache Yapılandırması

```python
# Redis cache kullanımı
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

FastAPICache.init(RedisBackend(redis_client), prefix="seo-cache")
```

## Güvenlik Kontrol Listesi

- [ ] `.env` dosyası `.gitignore`'da
- [ ] Güçlü SECRET_KEY kullanılıyor
- [ ] MongoDB authentication aktif
- [ ] Redis protected-mode aktif
- [ ] SSL/TLS sertifikaları geçerli
- [ ] Firewall kuralları yapılandırıldı
- [ ] Rate limiting aktif
- [ ] API Key'ler güvenli saklanıyor

## Destek ve Kaynaklar

- **GitHub Issues**: https://github.com/your-org/seo-command-center/issues
- **API Documentation**: http://localhost:8000/api/docs
- **Celery Monitoring**: http://localhost:5555

---

**Not**: Bu rehber sürekli güncellenmektedir. Son değişiklikler için CHANGELOG.md dosyasını kontrol edin.

**Versiyon**: 1.0.0
**Son Güncelleme**: 2026
