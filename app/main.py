from fastapi import FastAPI
from app.api.endpoints.chatbot import router as chatbot_router

app = FastAPI(title="AI Tax RAG Assistant - Backend")

app.include_router(chatbot_router)

@app.get("/")
def root():
    return {"message":"Welcome to the AI Tax Assistant"}