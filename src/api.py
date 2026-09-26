from fastapi import FastAPI
import uvicorn

from src.controllers.chat_controller import ChatController


app = FastAPI()
app.include_router(ChatController.create_router())

@app.get("/")
def read_root():
    return {"Hello": "World"}


if __name__ == "__main__":
    uvicorn.run("src.api:app", host="0.0.0.0", port=5000)
