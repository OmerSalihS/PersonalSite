# Deploying to Render

This guide will help you deploy your Flask portfolio application to Render.

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)

## Step-by-Step Deployment

### 1. Prepare Your Repository

Make sure your repository has these files (already included):
- `requirements.txt` - Python dependencies
- `render.yaml` - Render configuration
- `app.py` - Main application file

### 2. Create Render Services

#### Option A: Using render.yaml (Recommended)
1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click "New" → "Blueprint"
3. Connect your GitHub repository
4. Render will automatically detect the `render.yaml` file
5. Click "Apply" to create both the web service and database

#### Option B: Manual Setup
1. **Create Database First:**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "PostgreSQL"
   - Name: `portfolio-db`
   - Database Name: `portfolio`
   - User: `portfolio_user`
   - Click "Create Database"

2. **Create Web Service:**
   - Click "New" → "Web Service"
   - Connect your GitHub repository
   - Name: `portfolio-web`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn --bind :$PORT --workers 1 --worker-class eventlet --threads 8 --timeout 0 app:app`

3. **Add Environment Variables:**
   - In your web service settings, add:
     - `FLASK_ENV` = `production`
     - `PYTHONUNBUFFERED` = `1`
     - `DATABASE_URL` = (copy from your database's connection string)

### 3. Database Setup

The application will automatically:
- Detect it's running on Render (via `DATABASE_URL`)
- Switch from MySQL to PostgreSQL
- Create all necessary tables
- Insert initial data

### 4. Custom Domain (Optional)

1. In your web service settings
2. Go to "Settings" → "Custom Domains"
3. Add your domain name
4. Update your DNS records as instructed

## Environment Differences

| Feature | Local Development | Render Production |
|---------|------------------|-------------------|
| Database | MySQL | PostgreSQL |
| Debug Mode | Enabled | Disabled |
| Port | 8080 | Dynamic ($PORT) |
| SSL | No | Automatic |

## Troubleshooting

### Common Issues:

1. **Database Connection Errors**
   - Ensure `DATABASE_URL` environment variable is set
   - Check database credentials in Render dashboard

2. **Build Failures**
   - Check build logs in Render dashboard
   - Ensure all dependencies are in `requirements.txt`

3. **Application Won't Start**
   - Check start command is correct
   - Verify `app.py` is in root directory

### Checking Logs:
- Go to your web service in Render dashboard
- Click "Logs" tab to see real-time application logs

## Cost Information

**Free Tier Includes:**
- 750 compute hours/month
- PostgreSQL database with 1GB storage
- Automatic SSL certificates
- Custom domains

**Limitations:**
- Services sleep after 15 minutes of inactivity
- Takes 30+ seconds to wake up from sleep

## Post-Deployment

After successful deployment:
1. Test all functionality (piano, resume, chat)
2. Verify database is working (resume data loading)
3. Test user registration/login
4. Check all static files are loading

Your application will be available at: `https://your-service-name.onrender.com` 