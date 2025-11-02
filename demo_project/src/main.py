"""
FastAPI application entry point
"""
from fastapi import FastAPI
from .api import users, auth

app = FastAPI(
    title="Demo API",
    description="A demo API for LocalLLM Code testing",
    version="1.0.0"
)

# Include routers
app.include_router(users.router)
app.include_router(auth.router)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Demo API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
