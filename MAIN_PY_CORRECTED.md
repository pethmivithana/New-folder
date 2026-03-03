# Fixed main.py - CORS Configuration

## Complete Corrected File

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from contextlib import asynccontextmanager
from routes import space_routes, sprint_routes, backlog_routes, analytics_routes, ai_routes, impact_routes
from database import connect_db, close_db
from model_loader import model_loader


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await connect_db()
    print("\n" + "="*50)
    print("Loading ML Models...")
    print("="*50)
    try:
        models_loaded = model_loader.load_all_models()
        if models_loaded:
            print("\n✓ ML Models initialization complete\n")
        else:
            print("\n⚠ Warning: Some ML models failed to load")
            print("System will use fallback predictions\n")
    except Exception as e:
        print(f"\n⚠ Warning: ML model loading failed: {e}")
        print("System will use fallback predictions\n")
    
    yield
    
    # Shutdown
    await close_db()


app = FastAPI(
    title="Agile Management Tool API",
    lifespan=lifespan
)


# CORS Configuration - Add BEFORE routes are included
# Using explicit configuration for clarity and reliability
ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Length", "Content-Type"],
    max_age=3600,
)


# Include routers - After CORS middleware is configured
app.include_router(space_routes.router, prefix="/api/spaces", tags=["Spaces"])
app.include_router(sprint_routes.router, prefix="/api/sprints", tags=["Sprints"])
app.include_router(backlog_routes.router, prefix="/api/backlog", tags=["Backlog Items"])
app.include_router(analytics_routes.router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(ai_routes.router, prefix="/api/ai", tags=["AI Predictions"])
app.include_router(impact_routes.router, prefix="/api/impact", tags=["Impact Analysis"])


@app.get("/")
async def root():
    return {"message": "Agile Management Tool API"}


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "models_loaded": len(model_loader.models),
        "models": list(model_loader.models.keys())
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

## What Changed

1. **Added explicit ALLOWED_ORIGINS list** - Includes all common development ports (3000, 5173, 8000)
2. **Explicit allow_methods** - Changed from `["*"]` to explicit methods including OPTIONS for preflight
3. **Added max_age=3600** - Caches CORS preflight responses for 1 hour to reduce overhead
4. **Simplified expose_headers** - Removed unnecessary headers that FastAPI includes by default
5. **CORS middleware positioned correctly** - Added immediately after app creation but BEFORE route inclusion

## Testing

After updating, restart the backend:
```bash
python main.py
```

Then check CORS is working:
```bash
curl -H "Origin: http://localhost:5173" \
     -H "Access-Control-Request-Method: POST" \
     -H "Access-Control-Request-Headers: Content-Type" \
     -X OPTIONS \
     http://localhost:8000/api/spaces/
```

Should return 200 OK with proper Access-Control headers.
