# Coolify Deployment Guide

## Quick Fix for Current Issues

The deployment errors you're seeing are caused by:

1. **Missing migrate.py** - Fixed ✅
2. **Permission denied on ./data/uploads** - Fixed ✅

## Environment Variables Required in Coolify

Set these in your Coolify project environment variables:

```bash
# Required
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://postgres:password@postgres-db:5432/mini_video_factory

# Optional (Wasabi Storage)
WASABI_ENDPOINT=https://s3.ap-southeast-1.wasabisys.com
WASABI_REGION=ap-southeast-1
WASABI_BUCKET=backend-testing
WASABI_ACCESS_KEY_ID=your-access-key
WASABI_SECRET_ACCESS_KEY=your-secret-key
```

## Setting up PostgreSQL in Coolify

1. **Create PostgreSQL Database**:
   - In Coolify, go to "Databases" 
   - Create new PostgreSQL database
   - Note the connection details

2. **Set DATABASE_URL**:
   ```
   postgresql://username:password@hostname:5432/database_name
   ```

## Deployment Steps

1. **Push the fixes to your repository**
2. **In Coolify, set the environment variables above**
3. **Redeploy the application**

The app will now:
- ✅ Find the migrate.py file
- ✅ Create directories with proper permissions
- ✅ Use local PostgreSQL database on Coolify
- ✅ Run database migrations automatically
- ✅ Handle both local and cloud storage

## Files Changed

- ✅ Created `migrate.py` - handles database migrations
- ✅ Updated `Dockerfile` - fixes permission issues
- ✅ Updated `start.sh` - better error handling
- ✅ Updated `app.py` - graceful directory creation
- ✅ Created `.env.production` - production config template

## Testing

After deployment, check:
1. Health endpoint: `https://your-domain/health`
2. Login page: `https://your-domain/login`
3. Logs should show "Mini Video Factory starting up..." without errors

## Troubleshooting

If you still see issues:
1. Check Coolify logs for specific error messages
2. Verify DATABASE_URL is set correctly
3. Ensure PostgreSQL database is running and accessible
4. Check volume mounts are working: `./data:/app/data`
5. Verify database migrations ran successfully