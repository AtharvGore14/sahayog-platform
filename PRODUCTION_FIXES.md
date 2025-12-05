# Production Feature Fixes for Render Deployment

## Common Issues: Local Works, Production Doesn't

### 1. WebSocket Connections (Real-time Features)
**Problem**: WebSocket connections fail on Render because:
- Marketplace runs as subprocess on different port
- WebSocket routing not properly configured through proxy
- Redis connection issues

**Solution**: 
- WebSocket connections need to go directly to marketplace subprocess
- Use `wss://` for HTTPS in production
- Ensure Redis is properly configured

### 2. Database Migrations
**Problem**: Migrations might fail silently, causing features to break

**Solution**: Check build logs for migration errors, ensure DATABASE_URL is set

### 3. Static Files
**Problem**: Static files not loading correctly

**Solution**: Ensure collectstatic runs successfully, check STATIC_ROOT

### 4. API Endpoints
**Problem**: API calls fail due to CORS/CSRF issues

**Solution**: Already fixed with CORS_ALLOW_ALL_ORIGINS and CSRF exemption

### 5. Environment Variables
**Problem**: Missing environment variables cause features to fail

**Solution**: Ensure all required vars are set in render.yaml

## Quick Debugging Steps

1. Check Render logs for errors
2. Verify DATABASE_URL is set
3. Verify REDIS_URL is set  
4. Check if migrations ran successfully
5. Test API endpoints directly
6. Check WebSocket connections in browser console

