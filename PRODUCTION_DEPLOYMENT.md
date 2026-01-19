# 🚀 Production Deployment Guide - SECRET_KEY Configuration

## **Overview**
This guide explains how to properly deploy the Disease Prediction app to production with secure SECRET_KEY configuration.

---

## **1. Docker Deployment (Recommended)**

### **Create `Dockerfile`**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 5001

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5001", "--workers", "4", "run:app"]
```

### **Environment Variables in Docker Compose**
```yaml
version: '3.8'
services:
  app:
    build: .
    environment:
      - SECRET_KEY=${SECRET_KEY}
      - FLASK_ENV=production
      - DATABASE_URL=postgresql://user:pass@db:5432/disease_db
    ports:
      - "5001:5001"
    depends_on:
      - db
  db:
    image: postgres:15
    environment:
      POSTGRES_PASSWORD: ${DB_PASSWORD}
```

**Deploy:**
```bash
# Generate SECRET_KEY
export SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Build and run
docker-compose up -d
```

---

## **2. Heroku Deployment**

### **Step 1: Login & Create App**
```bash
heroku login
heroku create your-app-name
```

### **Step 2: Set Environment Variables**
```bash
# Generate secure key
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Set in Heroku
heroku config:set SECRET_KEY=$SECRET_KEY -a your-app-name
heroku config:set FLASK_ENV=production -a your-app-name
```

### **Step 3: Deploy**
```bash
git push heroku main
```

**Verify:**
```bash
heroku logs -a your-app-name --tail
```

---

## **3. AWS EC2 Deployment**

### **Step 1: Connect to Server**
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

### **Step 2: Install Dependencies**
```bash
sudo apt update
sudo apt install python3-pip python3-venv postgresql
```

### **Step 3: Deploy Application**
```bash
git clone https://github.com/your-username/Disease-prediction.git
cd Disease-prediction
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### **Step 4: Set Environment Variables**
```bash
# Generate SECRET_KEY
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# Create .env file
cat > .env << EOF
SECRET_KEY=$SECRET_KEY
FLASK_ENV=production
DATABASE_URL=postgresql://user:pass@localhost:5432/disease_db
EOF

# Secure permissions
chmod 600 .env
```

### **Step 5: Run with Gunicorn**
```bash
gunicorn --bind 0.0.0.0:5001 --workers 4 run:app
```

---

## **4. Google Cloud Run**

### **Create `Procfile`**
```
web: gunicorn -b :$PORT run:app
```

### **Deploy**
```bash
# Set SECRET_KEY in Cloud Run
gcloud run deploy disease-prediction \
  --source . \
  --set-env-vars SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))"),FLASK_ENV=production \
  --region us-central1 \
  --allow-unauthenticated
```

---

## **5. Environment Variables Management**

### **✅ DO:**
```bash
# ✅ Generate unique SECRET_KEY per environment
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# ✅ Store in environment variables (not in code)
export SECRET_KEY=your_generated_key_here

# ✅ Use different keys for dev, staging, prod
prod_secret=$(python -c "import secrets; print(secrets.token_hex(32))")
staging_secret=$(python -c "import secrets; print(secrets.token_hex(32))")
```

### **❌ DON'T:**
```bash
# ❌ Commit .env to git
git add .env

# ❌ Use same key everywhere
SECRET_KEY=production_key_123  # Same for dev & prod

# ❌ Hardcode in code
app.config['SECRET_KEY'] = 'my_secret_key'

# ❌ Use predictable keys
SECRET_KEY=password123
```

---

## **6. Deployment Checklist**

Before deploying to production:

- [ ] Generate unique `SECRET_KEY` with `secrets.token_hex(32)`
- [ ] Set `SECRET_KEY` in environment variables (not in code)
- [ ] Set `FLASK_ENV=production`
- [ ] Use production database (PostgreSQL recommended)
- [ ] Configure SSL/HTTPS certificates
- [ ] Set up monitoring and logging
- [ ] Configure backups
- [ ] Test in staging first
- [ ] Remove debug mode (`debug=False`)
- [ ] Use production WSGI server (Gunicorn, uWSGI)

---

## **7. Verifying Deployment**

```bash
# Check if SECRET_KEY is loaded
curl -X POST https://your-app.com/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "email=test@test.com&password=test"

# Check logs for errors
docker logs your-container-id

# Monitor security
heroku logs --tail
```

---

## **8. Rotating SECRET_KEY**

If compromised, rotate immediately:

```bash
# Generate new key
NEW_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")

# Update environment
export SECRET_KEY=$NEW_KEY

# Redeploy
docker-compose down && docker-compose up -d
# OR
heroku config:set SECRET_KEY=$NEW_KEY
# OR
systemctl restart app-service
```

---

## **Summary**

| Platform | Method | Command |
|----------|--------|---------|
| Docker | docker-compose | `docker-compose up -d` |
| Heroku | Git push | `git push heroku main` |
| AWS EC2 | SSH | `gunicorn --bind 0.0.0.0:5001` |
| Google Cloud Run | CLI | `gcloud run deploy` |
| DigitalOcean | Systemd | `systemctl start app` |

All methods require: `SECRET_KEY` in environment variables (never hardcoded).
