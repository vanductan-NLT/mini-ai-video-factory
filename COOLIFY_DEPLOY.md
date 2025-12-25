# Deploy Mini Video Factory với Coolify

## Bước 1: Chuẩn bị Repository
1. Push code lên GitHub repository của bạn
2. Đảm bảo có các file: `docker-compose.yml`, `Dockerfile`, `.env.example`

## Bước 2: Tạo Application trong Coolify

### 2.1 Tạo Resource mới
- Vào Coolify dashboard
- Click **"+ Add Resource"**
- Chọn **"Application"**
- Chọn **"Docker Compose"**

### 2.2 Config Repository
```
Repository URL: https://github.com/your-username/mini-video-factory
Branch: main
Build Pack: Docker Compose
```

### 2.3 Build Settings
```
Build Command: docker-compose build
Start Command: docker-compose up -d
Port: 8080
Health Check Path: /health
```

## Bước 3: Environment Variables

Thêm các biến môi trường sau trong Coolify:

### Required (Bắt buộc)
```bash
SECRET_KEY=your-generated-secret-key-here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-supabase-anon-key
```

### Optional (Tùy chọn)
```bash
# Wasabi Storage (bỏ trống để dùng local storage)
WASABI_ENDPOINT=https://s3.region.wasabisys.com
WASABI_REGION=us-east-1
WASABI_BUCKET=your-bucket-name
WASABI_ACCESS_KEY_ID=your-access-key
WASABI_SECRET_ACCESS_KEY=your-secret-key

# App Configuration
HOST_PORT=8080
FLASK_ENV=production
MAX_FILE_SIZE=104857600
MAX_DURATION=600
```

## Bước 4: Storage & Volumes

Trong Coolify, setup volumes:
```
./data:/app/data
./logs:/app/logs
```

## Bước 5: Domain & SSL

1. **Custom Domain** (optional):
   - Thêm domain trong Coolify settings
   - Point DNS A record đến server IP
   - Coolify tự động setup SSL

2. **Subdomain** (mặc định):
   - Coolify sẽ tạo subdomain tự động
   - Format: `app-name.your-coolify-domain.com`

## Bước 6: Deploy

1. Click **"Deploy"**
2. Theo dõi logs trong Coolify
3. Đợi build hoàn thành (~2-5 phút)
4. Access app qua URL được cung cấp

## 🔧 Management

### View Logs
- Trong Coolify dashboard → Application → Logs

### Restart Application
- Coolify dashboard → Application → Restart

### Update Application
- Push code mới lên GitHub
- Coolify tự động detect và redeploy
- Hoặc manual trigger deploy trong dashboard

### Environment Variables
- Coolify dashboard → Application → Environment
- Edit và restart để apply changes

## 🚨 Troubleshooting

### Build Failed
1. Check logs trong Coolify
2. Verify `docker-compose.yml` syntax
3. Ensure all required files exist

### App Not Starting
1. Check environment variables
2. Verify Supabase credentials
3. Check health endpoint: `/health`

### Storage Issues
1. Verify volumes are mounted correctly
2. Check disk space on server
3. Ensure write permissions

## 📊 Monitoring

Coolify provides:
- Real-time logs
- Resource usage metrics
- Health check status
- Deployment history

## 🎉 Success!

Sau khi deploy thành công:
- App sẽ chạy tại URL được Coolify cung cấp
- SSL certificate tự động
- Auto-restart nếu crash
- Easy scaling và management

**Lưu ý**: Coolify sẽ handle tất cả Docker, Nginx, SSL setup tự động. Bạn chỉ cần focus vào code!