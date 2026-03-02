# CORS Configuration & Troubleshooting

## What Was Fixed

### 1. Backend CORS Middleware (main.py)
- **Added explicit allowed origins**: localhost:5173, 127.0.0.1:5173, localhost:3000, 127.0.0.1:3000
- **Expanded allowed methods**: Added PATCH method for API consistency
- **Added max_age parameter**: Caches preflight OPTIONS requests for 1 hour to reduce overhead
- **Proper middleware ordering**: CORS middleware is applied before routes for correct functionality

### 2. Frontend API Client (api.js)
- **Added credentials flag**: `credentials: 'include'` ensures cookies are sent with cross-origin requests
- **Proper Content-Type header**: Already set to 'application/json' for JSON payloads

## How CORS Works

When the frontend (http://localhost:5173) makes a request to the backend (http://localhost:8000):

1. **Preflight Request**: Browser sends an OPTIONS request to check if the cross-origin request is allowed
2. **CORS Headers**: Backend responds with `Access-Control-Allow-Origin: http://localhost:5173`
3. **Actual Request**: If preflight succeeds, browser makes the actual POST/GET/DELETE request
4. **Response**: Backend returns data with proper CORS headers

## Testing CORS Locally

### Development Setup

**Terminal 1 - Start Backend:**
```bash
cd services/sprint_impact_service
python main.py
```
The backend will run on `http://localhost:8000`

**Terminal 2 - Start Frontend:**
```bash
cd frontend
npm install
npm run dev
```
The frontend will run on `http://localhost:5173`

### Verify CORS is Working

1. Open browser DevTools (F12)
2. Go to Network tab
3. Trigger an API call (e.g., click "Analyze Impact")
4. Look for the API request in Network tab
5. Click on the request and check Response Headers for:
   ```
   Access-Control-Allow-Origin: http://localhost:5173
   ```

## Common CORS Issues & Solutions

### Issue: "No 'Access-Control-Allow-Origin' header in response"

**Cause**: Backend CORS middleware not configured or in wrong order

**Solution**:
1. Verify CORS middleware in main.py is added BEFORE route includes
2. Check that your frontend URL is in `allow_origins` list
3. Restart backend server after changes

### Issue: "Credentials mode is 'include', but Access-Control-Allow-Credentials is missing"

**Cause**: Using `credentials: 'include'` but backend doesn't have `allow_credentials=True`

**Solution**: Ensure main.py has `allow_credentials=True` in CORSMiddleware config ✓ Already fixed

### Issue: "Method POST not allowed in CORS"

**Cause**: POST not in the `allow_methods` list

**Solution**: Check that `allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"]` ✓ Already fixed

## Production Deployment

For production (e.g., on Vercel or your own server):

1. Update `allow_origins` in main.py:
   ```python
   allow_origins=[
       "https://yourdomain.com",
       "https://app.yourdomain.com",
   ]
   ```

2. Update `API_BASE_URL` in api.js:
   ```javascript
   const API_BASE_URL = 'https://api.yourdomain.com/api';
   ```

3. For wildcard CORS (NOT recommended for production):
   ```python
   allow_origins=["*"],  # Only use if API is public with no auth
   allow_credentials=False,  # Must be False if using wildcard
   ```

## Browser & Network Considerations

- **Same-origin requests** (same host, protocol, port) bypass CORS entirely
- **Simple requests** (GET, HEAD, POST with simple headers) skip preflight for some browsers
- **Preflight caching** (`max_age=3600`) reduces OPTIONS requests from 2 per API call to 1 per hour per endpoint
- **Wildcard CORS** (`allow_origins=["*"]`) cannot be combined with `allow_credentials=True`

## Security Best Practices

1. **Never use wildcard for authenticated APIs** - Specify exact domains
2. **Use HTTPS in production** - Always use secure protocols
3. **Validate credentials** - Even with CORS allowed, validate on backend
4. **Set reasonable max_age** - Shorter = more secure but slower; current 3600s is reasonable
5. **Only allow necessary methods** - Don't use `["*"]` for methods if unnecessary

## Backend Routes Covered by CORS

All of these endpoints now work with frontend CORS:

- `/api/spaces/*` - Space management
- `/api/sprints/*` - Sprint operations
- `/api/backlog/*` - Backlog item operations
- `/api/impact/*` - Impact analysis (most important for your use case)
- `/api/analytics/*` - Analytics endpoints
- `/api/ai/*` - AI predictions

## Files Modified

1. `/services/sprint_impact_service/main.py` - Enhanced CORS middleware configuration
2. `/frontend/src/components/features/sprint_impact_service/api.js` - Added credentials flag
