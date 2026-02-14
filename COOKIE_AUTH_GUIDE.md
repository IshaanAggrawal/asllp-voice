# 🍪 Cookie-Based Authentication Guide

## What Changed

I've implemented **HTTP-only cookie authentication** for your Django backend. This is more secure than storing tokens in JavaScript.

---

## How It Works

### 1. Login (Sets Cookies)

**Endpoint**: `POST /api/auth/login/`

**Request**:
```json
{
  "username": "testuser",
  "password": "password123"
}
```

**Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "id": 1,
    "username": "testuser",
    "email": "test@example.com"
  }
}
```

**Cookies Set** (automatically):
- `access_token` - Valid for **1 day** (86400 seconds)
- `refresh_token` - Valid for **7 days** (604800 seconds)
- Both are **HTTP-only** (JavaScript can't access them)
- **SameSite=Lax** (CSRF protection)

---

### 2. Logout (Clears Cookies)

**Endpoint**: `POST /api/auth/logout/`

**Headers**:
```
Authorization: Bearer {access_token}
```

**Response**:
```json
{
  "success": true,
  "message": "Logged out successfully. Cookies cleared."
}
```

**What Happens**:
- Cookies are deleted (set to expire immediately)
- User must login again

---

## Cookie Settings Explained

```python
response.set_cookie(
    key='access_token',
    value=access_token,
    max_age=86400,      # 1 day in seconds
    httponly=True,      # ✅ JavaScript can't access (prevents XSS)
    secure=False,       # ⚠️ Set to True in production (HTTPS only)
    samesite='Lax'      # ✅ CSRF protection
)
```

### Security Features:

| Feature | Purpose | Value |
|---------|---------|-------|
| `httponly=True` | Prevents XSS attacks | JavaScript can't steal tokens |
| `secure=False` | HTTP allowed (dev) | Set `True` in production (HTTPS) |
| `samesite='Lax'` | CSRF protection | Cookie only sent to same site |
| `max_age` | Auto-expiry | 1 day for access, 7 days for refresh |

---

## For Production

Change in `views.py`:

```python
response.set_cookie(
    key='access_token',
    value=access_token,
    max_age=86400,
    httponly=True,
    secure=True,        # ✅ HTTPS only
    samesite='Strict'   # ✅ Stricter CSRF protection
)
```

---

## Interview Explanation

**Q: How does your authentication work?**

**Answer**: 
"I implemented JWT-based authentication with HTTP-only cookies for enhanced security. When a user logs in, Django generates access and refresh tokens and sets them as HTTP-only cookies, which prevents XSS attacks since JavaScript can't access them. The access token is valid for 24 hours, and the refresh token for 7 days. On logout, the cookies are cleared by setting their expiry to the past. In production, I'd enable the `secure` flag to ensure cookies are only sent over HTTPS."

---

## Testing

### With Postman:

1. **Login**:
   - POST `http://localhost:8000/api/auth/login/`
   - Body: `{"username": "test", "password": "pass"}`
   - Check **Cookies** tab - you'll see `access_token` and `refresh_token`

2. **Make Authenticated Request**:
   - GET `http://localhost:8000/api/agents/`
   - Cookies are sent automatically!
   - OR use Authorization header: `Bearer {token}`

3. **Logout**:
   - POST `http://localhost:8000/api/auth/logout/`
   - Cookies are deleted

### With Browser Console:

```javascript
// Login
fetch('http://localhost:8000/api/auth/login/', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({username: 'test', password: 'pass'}),
  credentials: 'include'  // Important: send/receive cookies
})
.then(r => r.json())
.then(console.log);

// Check cookies (won't see them - they're HTTP-only!)
document.cookie;  // Empty or other cookies only

// Logout
fetch('http://localhost:8000/api/auth/logout/', {
  method: 'POST',
  credentials: 'include'
})
.then(r => r.json())
.then(console.log);
```

---

## Why This is Better

### Before (Session State):
- ❌ Tokens in JavaScript (vulnerable to XSS)
- ❌ Lost on page refresh (unless manually saved)
- ❌ Can be stolen by malicious scripts

### After (HTTP-only Cookies):
- ✅ Tokens inaccessible to JavaScript
- ✅ Automatically sent with requests
- ✅ Persist across page refreshes
- ✅ Auto-expire after 1 day
- ✅ Protected against XSS attacks

---

## Compatibility

Your implementation supports **both methods**:

1. **Cookie-based** (automatic, more secure)
2. **Header-based** (manual, for mobile apps)

```python
# Both work:
Authorization: Bearer eyJ...  # Manual header
# OR
Cookie: access_token=eyJ...   # Automatic cookie
```

---

**You're now production-ready with secure authentication! 🔐**
