from fastapi import FastAPI
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from openai import OpenAI
import json
import os

client = OpenAI(api_key="OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    message: str


MEMORY_FILE = "memory.json"


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return []
    with open(MEMORY_FILE, "r") as f:
        return json.load(f).get("conversations", [])


def save_memory(conversations):
    with open(MEMORY_FILE, "w") as f:
        json.dump({"conversations": conversations}, f, indent=4)


@app.post("/chat")
async def chat(msg: Message):
    # Cargar memoria previa
    memory = load_memory()

    # Preparar mensajes para el modelo
    messages = [
        {"role": "system", "content": "Eres un amigo inteligente, amable, divertido. Ayudas con tareas, matemáticas e idiomas."}
    ]

    # agregar memoria al prompt
    for m in memory:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["bot"]})

    # mensaje actual
    messages.append({"role": "user", "content": msg.message})

    # llamar a OpenAI
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    bot_reply = response.choices[0].message.content

    # guardar memoria
    memory.append({
        "user": msg.message,
        "bot": bot_reply
    })
    save_memory(memory)

    return {"reply": bot_reply}

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))

