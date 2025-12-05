# 🚀 SAHAYOG AI MARKETPLACE - STARTING GUIDE

## 📋 QUICK START (EASIEST WAY)

### **Option 1: One-Click Launch (RECOMMENDED)**
**Double-click:** `START_MARKETPLACE.bat`
- Automatically starts Django server
- Opens marketplace in browser
- Shows all access information

### **Option 2: Direct Access (No Server)**
**Double-click:** `LAUNCH_MARKETPLACE.html`
- Works immediately without server
- Real marketplace with your listings
- Perfect for testing

### **Option 3: Frontend Only**
**Double-click:** `ai_enhanced_frontend.html`
- Direct access to marketplace
- Works with or without server

---

## 🔧 DETAILED STARTING PROCEDURE

### **Method 1: Full Backend Mode (Complete Features)**

#### **Step 1: Start Django Server**
**Option A: Using Batch File (Easiest)**
```
Double-click: START_SERVER.bat
```

**Option B: Manual Start**
1. Open **Command Prompt** or **PowerShell**
2. Navigate to project folder:
   ```
   cd C:\Users\mayan\Documents\sahayog_marketplace
   ```
3. Activate virtual environment:
   ```
   venv\Scripts\activate
   ```
4. Start Django server:
   ```
   python manage.py runserver 127.0.0.1:8000
   ```

#### **Step 2: Open Marketplace**
- **Double-click:** `LAUNCH_MARKETPLACE.html`
- **OR** Open browser and go to: `http://127.0.0.1:8000`

#### **Step 3: Login**
Use any of these accounts:
- **DemoS** (Seller) / demo123
- **DemoB** (Buyer) / demo123
- **admin** / admin123

---

### **Method 2: Demo Mode (No Server Required)**

#### **Step 1: Open Marketplace**
**Double-click:** `LAUNCH_MARKETPLACE.html`

#### **Step 2: Login**
- **DemoS** (Seller) / demo123
- **DemoB** (Buyer) / demo123

#### **Step 3: Start Trading!**
- Create listings as seller
- View and bid as buyer
- All features work without server

---

## 🎯 TESTING THE MARKETPLACE

### **Complete Workflow Test:**

1. **Launch Marketplace**
   - Double-click `LAUNCH_MARKETPLACE.html`

2. **Login as Seller (DemoS)**
   - Username: `DemoS`
   - Password: `demo123`
   - Click "Sign In"

3. **Create a Listing**
   - Fill out the form:
     - Commodity name (e.g., "Cardboard")
     - Quantity (e.g., "500")
     - Starting price (e.g., "15.00")
     - Quality score (e.g., "0.85")
     - Auction end time
   - Click "Publish AI-Optimized Listing"

4. **Logout and Login as Buyer (DemoB)**
   - Click logout
   - Username: `DemoB`
   - Password: `demo123`
   - Click "Sign In"

5. **View Your Listing**
   - Your listing should appear in the buyer dashboard
   - Click on it to view details
   - Place a bid!

---

## 🔑 AVAILABLE ACCOUNTS

| Role | Username | Password | Purpose |
|------|----------|----------|---------|
| **Seller** | **DemoS** | demo123 | Create listings |
| **Buyer** | **DemoB** | demo123 | View and bid |
| Admin | admin | admin123 | Admin access |
| Seller | eco_seller | demo123 | Additional seller |
| Buyer | green_recycler | demo123 | Additional buyer |

---

## ⚙️ ADVANCED: Full Server Setup (Optional)

For complete AI features and real-time updates:

### **1. Start Redis Server**
```
redis-server
```

### **2. Start Django Server**
```
Double-click: START_SERVER.bat
```

### **3. Start Celery Worker** (New Terminal)
```
venv\Scripts\activate
celery -A sahayog_marketplace worker -l info --pool=solo
```

### **4. Start Celery Beat** (New Terminal)
```
venv\Scripts\activate
celery -A sahayog_marketplace beat -l info
```

---

## 🐛 TROUBLESHOOTING

### **Problem: "ModuleNotFoundError: No module named 'django'"**
**Solution:** Activate virtual environment first:
```
venv\Scripts\activate
```

### **Problem: "Server not connected"**
**Solution:** 
- Start Django server: `START_SERVER.bat`
- OR use demo mode (works without server)

### **Problem: "Port 8000 already in use"**
**Solution:**
- Close other Django servers
- OR use different port: `python manage.py runserver 127.0.0.1:8001`

### **Problem: Listings not appearing**
**Solution:**
- Make sure you're logged in as different user (seller vs buyer)
- Refresh the page
- Check browser console for errors

---

## ✅ QUICK CHECKLIST

- [ ] Double-click `LAUNCH_MARKETPLACE.html`
- [ ] Login with DemoS or DemoB
- [ ] Create listing (as seller) or view listings (as buyer)
- [ ] Test bidding functionality

---

## 🎉 YOU'RE READY!

**Just double-click `LAUNCH_MARKETPLACE.html` and start trading!**

For questions or issues, check the `README.md` file.

**Happy Trading! 🚀**
