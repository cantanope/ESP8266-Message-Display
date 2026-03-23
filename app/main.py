from fastapi import FastAPI, HTTPException, Security, Request
from fastapi.security import APIKeyHeader
import random
import json
from datetime import datetime
import pytz
from dotenv import load_dotenv
import os
from fastapi.middleware.cors import CORSMiddleware


# Retreive API key from .env file
load_dotenv()
API_KEY = os.getenv("API_KEY")

app = FastAPI()

api_key_header = APIKeyHeader(name="X-API-Key")

# Set Timezone 
timeZone = pytz.timezone("America/Vancouver")

# CORS Middleware to allow requests from any origin
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

# Alternate CORS Middleware using FastAPI's built-in CORSMiddleware, not sure if this is necessary since the above middleware already sets the headers, but it doesn't hurt to have both
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["X-API-Key", "Content-Type"],
)

def verify_api_key(key: str = Security(api_key_header)):
    if key != API_KEY:
        raise HTTPException(status_code=403, detail="Invalid API Key")
    return key

# Default message endpoint, returns a random message from messages.json, but if there is a current message in livemessage.json that has not expired, it will return that instead
@app.get("/v1/messages/")
def get_message(api_key: str = Security(verify_api_key)):
    livewMessageFile = open("./livemessage.json", "r")
    liveMessage = json.load(livewMessageFile)

    if liveMessage["currentTime"] != "None":
        now = datetime.now()
        messageTime = datetime.strptime(liveMessage["currentTime"], "%Y-%m-%d %H:%M:%S")
        timeDifference = (now.replace(tzinfo=None) - messageTime.replace(tzinfo=None)).total_seconds()
        if timeDifference < int(liveMessage["displayTimeSeconds"]):
            return {"line_one": liveMessage["line_one"], 
                    "line_two": liveMessage["line_two"], 
                    "displayTimeSeconds": liveMessage["displayTimeSeconds"], 
                    "currentTime": liveMessage["currentTime"], 
                    "serverTime": now.replace(tzinfo=None).strftime("%Y-%m-%d %H:%M:%S"), 
                    "timeDifference": timeDifference,}
    
    messageFile = open("./messages.json", "r")
    messages = json.load(messageFile)
    messageindex = random.randint(0, len(messages) - 1)
    return messages[messageindex]

# Endpoint to return all messages in messages.json, this is mostly for debugging purposes but it could also be used to display all messages on a website or something
@app.get("/v1/messages/all")
def get_all_messages(api_key: str = Security(verify_api_key)):
    messageFile = open("./messages.json", "r")
    messages = json.load(messageFile)
    return {"messages": messages}

# Endpoint to add a new message to messages.json, it checks if the message already exists and if the lines are less than 16 characters long before adding it to the file
@app.post("/v1/messages/{line_one}/{line_two}")
def push_message(line_one: str, line_two: str, api_key: str = Security(verify_api_key)):
    if len(line_one) > 16 or len(line_two) > 16:
        raise HTTPException(status_code=400, detail="Line one and line two must be less than 16 characters long")
    for message in json.load(open("./messages.json", "r")):
        if line_one.strip() == message["line_one"].strip() and line_two.strip() == message["line_two"].strip():
            raise HTTPException(status_code=400, detail="Message already exists")
    messageFile = open("./messages.json", "r") 
    messages = json.load(messageFile)
    messages.append({"line_one": line_one, "line_two": line_two})
    with open("./messages.json", "w") as f:
        json.dump(messages, f, indent=2)
    return {"message": {"line_one": line_one, "line_two": line_two},"status": "success"}        

# Endpoint to push a live message to livemessage.json, this will overwrite any existing live message, 
# it checks if the lines are less than 16 characters long before adding it to the file, 
# it also adds the current time to the file so that the get_message endpoint can check if the message has expired or not
@app.post("/v1/messages/{line_one}/{line_two}/{displayTimeSeconds}")
def push_current_message(line_one: str, line_two: str, displayTimeSeconds: int, api_key: str = Security(verify_api_key)):
    now = datetime.now()
    if len(line_one) > 16 or len(line_two) > 16:
        raise HTTPException(status_code=400, detail="Line one and line two must be less than 16 characters long")
    with open ("./livemessage.json", "w") as f:
        json.dump(
            {"line_one": line_one, 
             "line_two": line_two, 
             "displayTimeSeconds": displayTimeSeconds, 
             "currentTime": now.strftime("%Y-%m-%d %H:%M:%S")
            }, f, indent=2)
    return {"message": 
            {"line_one": line_one, 
             "line_two": line_two
            },
            "displayTimeSeconds": displayTimeSeconds,
            "currentTime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "status": "success"}