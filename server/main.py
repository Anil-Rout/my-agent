# FastAPI Server - connects desktop and mobile apps
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from server.routes import chat, actions, system

app = FastAPI(title="My AI Agent", version="1.0.0")

# Allow all connections (desktop + mobile)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all routes
app.include_router(chat.router,    prefix="/chat",    tags=["Chat"])
app.include_router(actions.router, prefix="/actions", tags=["Actions"])
app.include_router(system.router,  prefix="/system",  tags=["System"])

@app.get("/")
def home():
    return {"status": "Agent is running", "version": "1.0.0"}
