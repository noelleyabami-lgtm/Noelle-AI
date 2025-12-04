from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
import uvicorn
import json
import os

client = OpenAI(api_key="OPENAI_API_KEY")

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------- ARCHIVOS ---------
USERS_FILE = "users.json"

# --------- MODELOS ---------
class Register(BaseModel):
    username: str
    password: str

class Login(BaseModel):
    username: str
    password: str

class Message(BaseModel):
    username: str
    text: str

# --------- FUNCIONES ---------
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)

# --------- ENDPOINTS ---------

# REGISTRO
@app.post("/register")
async def register(data: Register):
    users = load_users()

    if data.username in users:
        raise HTTPException(status_code=400, detail="El usuario ya existe.")

    users[data.username] = {
        "password": data.password,
        "memory": []
    }
    save_users(users)

    return {"message": "Cuenta creada con éxito."}


# LOGIN
@app.post("/login")
async def login(data: Login):
    users = load_users()

    if data.username not in users or users[data.username]["password"] != data.password:
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos.")

    return {"message": "Login exitoso."}


# CHAT
@app.post("/chat")
async def chat(data: Message):
    users = load_users()

    if data.username not in users:
        raise HTTPException(status_code=401, detail="Usuario no encontrado.")

    # memoria individual del usuario
    memory = users[data.username]["memory"]

    # construir mensajes del chat
    messages = [{"role": "system", "content": "Eres un amigo inteligente y divertido."}]

    for m in memory:
        messages.append({"role": "user", "content": m["user"]})
        messages.append({"role": "assistant", "content": m["bot"]})

    messages.append({"role": "user", "content": data.text})

    # llamada al modelo
    response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
    )

    bot_reply = response.choices[0].message.content

    # guardar en memoria del usuario
    memory.append({"user": data.text, "bot": bot_reply})
    users[data.username]["memory"] = memory
    save_users(users)

    return {"reply": bot_reply}


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=10000)
