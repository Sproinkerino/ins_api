# Deployment Guide for DigitalOcean

## 1. Server Setup

1. Create a new Ubuntu droplet on DigitalOcean
2. SSH into your server:
```bash
ssh root@your-server-ip
```

## 2. Install Required Packages

```bash
# Update package list
apt update
apt upgrade -y

# Install required packages
apt install -y python3-pip python3-venv nginx supervisor

# Create required directories
mkdir -p /var/www/chatbot_api
mkdir -p /var/log/django
mkdir -p /var/log/gunicorn
chown -R www-data:www-data /var/log/django
chown -R www-data:www-data /var/log/gunicorn
```

## 3. Clone and Setup Application

```bash
# Clone repository
cd /var/www/chatbot_api
git clone https://github.com/Sproinkerino/ins_api.git .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

## 4. Configure Application

1. Update production_settings.py with your server IP/domain
2. Set up environment variables in chatbot.service
3. Copy service file:
```bash
cp chatbot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable chatbot
systemctl start chatbot
```

## 5. Configure Nginx

Create `/etc/nginx/sites-available/chatbot`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        root /var/www/chatbot_api;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then:
```bash
ln -s /etc/nginx/sites-available/chatbot /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

## 6. SSL Setup (Optional but Recommended)

```bash
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

## 7. Final Steps

1. Collect static files:
```bash
python manage.py collectstatic
```

2. Apply migrations:
```bash
python manage.py migrate
```

3. Test your application:
```bash
curl https://your-domain.com/api/chat/
```

## Maintenance

- View logs:
```bash
tail -f /var/log/django/debug.log
tail -f /var/log/gunicorn/error.log
```

- Restart services:
```bash
systemctl restart chatbot
systemctl restart nginx
``` 