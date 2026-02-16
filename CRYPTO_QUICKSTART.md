# 🚀 Quick Start - Crypto Payment Integration

## ✅ Installation Complete!

All files have been created and the system is ready to use.

---

## 📋 What Was Added:

### New Files:
1. ✅ `templates/buy-crypto.html` - Crypto payment page
2. ✅ `requirements.txt` - Python dependencies
3. ✅ `CRYPTO_PAYMENT_GUIDE.md` - Full documentation

### Modified Files:
1. ✅ `app.py` - Added crypto payment endpoints
2. ✅ `templates/home.html` - Added crypto payment button

---

## 🎯 Test It Now:

### Step 1: Start the Server
```bash
cd C:\Users\sameh\Desktop\ALPHA
python app.py
```

### Step 2: Open in Browser
```
http://localhost:5000
```

### Step 3: Test Flow
1. **Login** with existing account
2. Click **"💰 Pay with Crypto (No KYC)"** button
3. Select cryptocurrency (BTC/ETH/USDT/LTC)
4. Click **"Create Payment"**
5. You'll see:
   - Payment address
   - Exact amount to send
   - QR code for scanning
   - Live status updates

---

## 💡 Key Features:

✅ **6 Cryptocurrencies Supported**
- Bitcoin (BTC)
- Ethereum (ETH)  
- USDT (TRC20)
- Litecoin (LTC)
- BNB (BSC)
- USDC (BSC)

✅ **Auto Status Checking**
- Checks every 10 seconds
- Auto-redirects on confirmation

✅ **No KYC Required**
- Completely anonymous
- No personal information needed

✅ **Instant Access**
- Payment confirmed → Access granted automatically
- Webhook updates users.json

---

## 🔑 Your NOWPayments API Key:
```
YEW353V-HP0MM01-G4QA7WX-MPDTF62
```
Already configured in `app.py`

---

## 🌐 Deployment (When Ready):

### For Render.com:
1. Push code to GitHub
2. Create new Web Service on Render
3. **Important**: Update webhook URL in `app.py` line 290:
   ```python
   "ipn_callback_url": "https://YOUR-APP-NAME.onrender.com/nowpayments-webhook"
   ```
4. Add to `requirements.txt`:
   ```
   gunicorn==21.2.0
   ```
5. Set Start Command: `gunicorn app:app`

---

## 🧪 Test Webhook Locally:

Since webhooks need HTTPS, test manually:

```bash
curl -X POST http://localhost:5000/nowpayments-webhook -H "Content-Type: application/json" -d "{\"payment_id\": 12345, \"payment_status\": \"confirmed\", \"order_description\": \"ALPHA Course - User 1\"}"
```

Check `users.json` - User 1 should have `"has_paid": true`

---

## 📊 Current Settings:

| Setting | Value |
|---------|-------|
| Course Price | $99 USD |
| Status Check Interval | 10 seconds |
| Webhook URL | https://alpha-project.onrender.com/nowpayments-webhook |
| Session Required | Yes (login required) |

---

## 🎨 UI Features:

- ✅ Glassmorphism design matching existing theme
- ✅ Responsive crypto selection grid
- ✅ Real-time QR code generation
- ✅ One-click address copy
- ✅ Animated status badges
- ✅ Auto-redirect on success

---

## ⚡ Everything is Ready!

The crypto payment system is **fully integrated** and ready to use.

For detailed documentation, see: `CRYPTO_PAYMENT_GUIDE.md`
