from fastapi import FastAPI
from .api import api_router

# Create app
app = FastAPI()
app.include_router(api_router)

@app.get('/')
async def index():
    return {'status': 'FastAPI application running.'}