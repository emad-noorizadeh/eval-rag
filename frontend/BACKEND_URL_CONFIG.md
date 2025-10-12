# 🔧 Backend URL Configuration Guide

**Author:** Emad Noorizadeh  
**Date:** 2025-01-27  
**Version:** 1.0

## 🚀 Quick Configuration

### **Method 1: Environment Variable (Recommended)**

Create or update `frontend/.env.local`:
```bash
# Backend API Configuration
NEXT_PUBLIC_BACKEND_URL=http://your-backend-server:9000
```

### **Method 2: Environment Variable for API Routes**

Create or update `frontend/.env.local`:
```bash
# Backend API Configuration (for API routes)
BACKEND_URL=http://your-backend-server:9000
NEXT_PUBLIC_BACKEND_URL=http://your-backend-server:9000
```

## 📁 Files That Support Environment Variables

### **✅ Already Configured (No Changes Needed):**
- `frontend/src/app/api/chat-config/route.ts`
- `frontend/src/app/api/chunking-config/route.ts`
- `frontend/src/app/api/documents/route.ts`
- `frontend/src/app/api/documents/[filename]/content/route.ts`
- `frontend/src/app/api/documents/[filename]/metadata/route.ts`

### **✅ Updated to Use Centralized Config:**
- `frontend/src/services/sessionService.ts`
- `frontend/src/config/api.ts` (new centralized configuration)

## 🔧 Configuration Examples

### **Local Development:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:9000
```

### **Production Server:**
```bash
NEXT_PUBLIC_BACKEND_URL=https://your-api-server.com
```

### **Docker/Container:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://backend:9000
```

### **Custom Port:**
```bash
NEXT_PUBLIC_BACKEND_URL=http://localhost:8080
```

## 🛠️ Manual Configuration (If Needed)

If you need to update hardcoded URLs manually, check these files:

### **Files with Hardcoded URLs:**
- `frontend/src/components/ChatInterface.tsx` (line 163)
- `frontend/src/components/DocumentList.tsx` (lines 89, 104, 136, 155, 181)
- `frontend/src/components/DocumentUpload.tsx` (lines 46, 62)
- `frontend/src/components/QueryInterface.tsx` (line 41)

### **Update Pattern:**
Replace:
```typescript
const response = await fetch('http://localhost:9000/endpoint', {
```

With:
```typescript
import { API_ENDPOINTS } from '../config/api';

const response = await fetch(API_ENDPOINTS.ENDPOINT_NAME, {
```

## 🧪 Testing Configuration

### **1. Check Environment Variables:**
```bash
cd frontend
echo $NEXT_PUBLIC_BACKEND_URL
```

### **2. Test API Connection:**
```bash
curl http://your-backend-server:9000/health
```

### **3. Check Browser Console:**
Look for any CORS or connection errors in the browser console.

## 📋 Configuration Checklist

- [ ] Set `NEXT_PUBLIC_BACKEND_URL` in `.env.local`
- [ ] Set `BACKEND_URL` in `.env.local` (for API routes)
- [ ] Restart development server: `npm run dev`
- [ ] Test API connection
- [ ] Check browser console for errors
- [ ] Verify all features work correctly

## ⚠️ Important Notes

1. **Environment Variables**: Use `NEXT_PUBLIC_` prefix for client-side variables
2. **API Routes**: Use `BACKEND_URL` for server-side API routes
3. **Restart Required**: Always restart the development server after changing environment variables
4. **CORS**: Ensure your backend allows requests from your frontend domain
5. **HTTPS**: Use HTTPS in production for security

## 🎯 Quick Start

1. **Create `.env.local`:**
   ```bash
   cd frontend
   echo "NEXT_PUBLIC_BACKEND_URL=http://localhost:9000" > .env.local
   echo "BACKEND_URL=http://localhost:9000" >> .env.local
   ```

2. **Restart Server:**
   ```bash
   npm run dev
   ```

3. **Test Connection:**
   Open browser and check if the app connects to your backend.

**Your backend URL is now configurable!** 🚀
