from fastapi import FastAPI, Response, status
from fastapi_controllers import Controller, post
from pydantic import BaseModel
from src.services.chat.chat_service import ChatService

class ChatRequest(BaseModel):
    userId: str
    q: str


class ChatController(Controller):
    prefix = "/chat"
    tags = ["chat"]

    def __init__(self) -> None:
        super().__init__()
        self._chat_service = ChatService()

    @post("/")
    async def perform_chat(self, request: ChatRequest):
        return await self._chat_service.perform_prompt(request.userId, request.q)
