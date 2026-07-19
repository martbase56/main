from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import auth, products, orders, admin, gmail, instagram, telegram, facebook

app = FastAPI(
    title="MerketBaseBD Premium API Platform",
    description="E-commerce, Dropshipping, Task and Social Promotion Management Hub.",
    version="1.2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(products.router, prefix="/api/products", tags=["Products"])
app.include_router(orders.router, prefix="/api/orders", tags=["Orders"])
app.include_router(admin.router, prefix="/api/admin", tags=["Admin Panel"])
app.include_router(gmail.router, prefix="/api/gmail", tags=["Gmail Tasks"])
app.include_router(instagram.router, prefix="/api/instagram", tags=["Instagram Tasks"])
app.include_router(telegram.router, prefix="/api/telegram", tags=["Telegram Services"])
app.include_router(facebook.router, prefix="/api/facebook", tags=["Facebook Tasks"])

@app.get("/api")
def read_api_root():
    return {
        "status": "success",
        "message": "MerketBaseBD API is running successfully!",
        "version": "1.2.0"
    }
