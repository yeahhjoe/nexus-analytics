from fastapi import FastAPI

app = FastAPI(title="Nexus Analytics", version="0.1.0")

@app.get("/")
async def root():
    return {"message": "Welcome to Nexus Analytics Service"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
