# import os
# import traceback
# from typing import List, Dict
# from pymongo import MongoClient
# from dotenv import load_dotenv
# from datetime import datetime
# from fastapi import FastAPI, HTTPException, Query, Request
# from pydantic import BaseModel
# from fastapi.middleware.cors import CORSMiddleware
# import anthropic
# import groq
# from utils.email_utils import send_email, format_conversation_for_email

# app = FastAPI()

# # === Load environment ===
# load_dotenv()
# CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
# GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# MONGO_URI = os.getenv("MONGODB_URI")
# DB_NAME = os.getenv("DB_NAME")
# COLLECTION_NAME = os.getenv("COLLECTION_NAME")

# if not GROQ_API_KEY:
#     raise ValueError("❌ GROQ_API_KEY missing in .env")
# if not MONGO_URI:
#     raise ValueError("❌ MONGODB_URI missing in .env")
# if not DB_NAME:
#     raise ValueError("❌ DB_NAME missing in .env")
# if not COLLECTION_NAME:
#     raise ValueError("❌ COLLECTION_NAME missing in .env")

# # === Clients ===
# client_claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
# client_groq = groq.Groq(api_key=GROQ_API_KEY)

# # === MongoDB Setup ===
# mongo_client = MongoClient(MONGO_URI)
# db = mongo_client[DB_NAME]
# collection = db[COLLECTION_NAME]

# # === Load context ===
# CONTEXT_FILE = "Pml_queries.txt"

# def load_context(filepath: str, max_chars: int = 3000) -> str:
#     try:
#         with open(filepath, "r", encoding="utf-8") as f:
#             context = f.read()[:max_chars]
#             print("📄 Loaded context (first 200 chars):", context[:200])
#             return context
#     except Exception as e:
#         print(f"⚠️ Failed to load context: {e}")
#         return ""

# context_text = load_context(CONTEXT_FILE)

# # === FastAPI Setup ===
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # === Models ===
# class UserInput(BaseModel):
#     message: str
#     role: str = "user"
#     conversation_id: str

# class InteractionLog(BaseModel):
#     conversation_id: str
#     user_name: str
#     mobile_number: str
#     event_type: str
#     metadata: Dict
#     timestamp: str

# class EmailSummaryRequest(BaseModel):
#     conversation_id: str
#     recipient: str = "abhishek.singh@paulmerchants.net"

# # === Core Logic ===

# def save_message(conversation_id: str, role: str, content: str):
#     collection.insert_one({
#         "conversation_id": conversation_id,
#         "role": role,
#         "content": content,
#         "timestamp": datetime.utcnow()
#     })

# def load_conversation(conversation_id: str) -> List[Dict[str, str]]:
#     try:
#         messages = list(collection.find(
#             {"conversation_id": conversation_id, "role": {"$exists": True}, "content": {"$exists": True}},
#             sort=[("timestamp", 1)]
#         ))
#         return [{"role": m["role"], "content": m["content"]} for m in messages]
#     except Exception as e:
#         print(f"[ERROR] Failed to load conversation from MongoDB: {e}")
#         return []

# # === Summarization ===
# async def summarize_messages(messages: List[Dict[str, str]]) -> str:
#     try:
#         chat_prompt = "".join([f"{m['role'].capitalize()}: {m['content']}\n" for m in messages])
#         if client_claude:
#             msg = client_claude.messages.create(
#                 model="claude-3-opus-20240229",
#                 max_tokens=200,
#                 temperature=0.3,
#                 messages=[{ "role": "user", "content": f"Summarize this chat into exactly 3 short and simple bullet points. Be concise and user-friendly.\n{chat_prompt}" }]
#             )
#             reply = msg.content[0].text.strip()
#             print("🤖 PaulBot Reply:\n", reply)
#             return reply
#     except Exception as e:
#         print(f"⚠️ Summarization failed: {e}")
#     return "[Summary unavailable]"

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to PaulBot (Claude/Groq). Use POST /chat/ to talk."}

# @app.post("/chat/")
# async def chat(input: UserInput):
#     try:
#         if input.message.lower().strip() == "others":
#             new_id = str(datetime.utcnow().timestamp()).replace('.', '')
#             return { "response": "Sure! How can I help you 😎?", "conversation_id": new_id }

#         print(f"[DEBUG] Loading conversation ID: {input.conversation_id}")
#         full_history = load_conversation(input.conversation_id)

#         if not any(m["role"] == "system" for m in full_history):
#             full_history.insert(0, {
#                 "role": "system",
#                 "content": f"You are PaulBot — a helpful assistant. Use this context:\n\n{context_text}"
#             })

#         full_history.append({ "role": input.role, "content": input.message })

#         total_chars = sum(len(m["content"]) for m in full_history)

#         prompt_intro = (
#             "You are PaulBot — a helpful assistant for Paul Merchants customers.\n"
#             "Always use very short, clear language.\n"
#             "When explaining, prefer only 2 or 3 bullet points.\n"
#             "Avoid writing long paragraphs unless the user explicitly asks for detailed information.\n"
#             "Make it easy for any customer to quickly understand.\n\n"
#         )

#         if total_chars > 12000:
#             summary = await summarize_messages(full_history[:-10])
#             prompt = prompt_intro + f"Summary of previous conversation:\n{summary}\n\nRecent messages:\n"
#             for msg in full_history[-10:]:
#                 prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
#         else:
#             prompt = prompt_intro + "".join([f"{m['role'].capitalize()}: {m['content']}\n" for m in full_history])

#         reply = None
#         if client_claude:
#             try:
#                 msg = client_claude.messages.create(
#                     model="claude-3-opus-20240229",
#                     max_tokens=600,
#                     temperature=0.7,
#                     messages=[{ "role": "user", "content": prompt }]
#                 )
#                 reply = msg.content[0].text.strip()
#             except Exception as e:
#                 print("⚠️ Claude failed, switching to Groq. Error:", e)

#         if not reply:
#             try:
#                 response = client_groq.chat.completions.create(
#                     model="llama3-70b-8192",
#                     messages=[{ "role": "user", "content": prompt }],
#                     max_tokens=600,
#                     temperature=0.7
#                 )
#                 reply = response.choices[0].message.content.strip()
#             except Exception as e:
#                 print("❌ Groq call failed:", e)
#                 raise HTTPException(status_code=500, detail="Both Claude and Groq failed.")

#         save_message(input.conversation_id, input.role, input.message)
#         save_message(input.conversation_id, "assistant", reply)

#         # ✅ Email trigger based on PaulBot message
#         # trigger_phrases = [
#         #     "If you don't see what you're looking for, click on your preferred choice and explore more options on our website: PML Holidays Website. Our team will connect with you shortly to curate the perfect trip for you!",
#         #     "Thank you! We will contact you shortly."
#         # ]

#         # if any(trigger_phrase.lower() in reply.lower() for trigger_phrase in trigger_phrases):
#         messages = list(collection.find(
#             {"conversation_id": input.conversation_id},
#             sort=[("timestamp", 1)]
#         ))
#         email_html = format_conversation_for_email(messages)
#         send_email(
#             subject=f"PaulBot Chat Summary - ID: {input.conversation_id}",
#             html_content=email_html,
#             recipient="abhishek.singh@paulmerchants.net"
#         )

#         return {"response": reply, "conversation_id": input.conversation_id}

#     except HTTPException as http_exc:
#         raise http_exc
#     except Exception as e:
#         traceback.print_exc()
#         raise HTTPException(status_code=500, detail=f"Unhandled server error: {str(e)}")

# @app.post("/send-email/")
# def trigger_email(conversation_id: str = Query(...), recipient: str = Query(...)):
#     messages = list(collection.find({"conversation_id": conversation_id}))
#     if not messages:
#         raise HTTPException(status_code=404, detail="Conversation not found.")
#     email_html = format_conversation_for_email(messages)
#     send_email(
#         subject=f"PaulBot Chat Summary - ID: {conversation_id}",
#         html_content=email_html,
#         recipient=recipient
#     )
#     return {"status": "Email sent"}

# @app.post("/send-email-summary/")
# async def send_summary(data: EmailSummaryRequest):
#     try:
#         messages = list(collection.find(
#             {"conversation_id": data.conversation_id},
#             sort=[("timestamp", 1)]
#         ))
#         if not messages:
#             raise HTTPException(status_code=404, detail="Conversation not found.")
#         email_html = format_conversation_for_email(messages)
#         send_email(
#             subject=f"PaulBot Conversation Summary - ID: {data.conversation_id}",
#             html_content=email_html,
#             recipient=data.recipient
#         )
#         return {"status": "Email summary sent"}
#     except Exception as e:
#         print("Error sending email summary:", e)
#         raise HTTPException(status_code=500, detail="Error sending summary email")

# @app.post("/log-interaction/")
# async def log_interaction(data: InteractionLog):
#     try:
#         collection.insert_one({
#             "type": "interaction",
#             "conversation_id": data.conversation_id,
#             "user_name": data.user_name,
#             "mobile_number": data.mobile_number,
#             "event_type": data.event_type,
#             "metadata": data.metadata,
#             "timestamp": data.timestamp
#         })
#         return {"status": "ok"}
#     except Exception as e:
#         print("Error saving interaction log:", e)
#         raise HTTPException(status_code=500, detail="Logging failed")

# @app.get("/chat-history/{conversation_id}")
# def get_chat_history(conversation_id: str):
#     try:
#         messages = list(collection.find(
#             {"conversation_id": conversation_id, "type": {"$ne": "interaction"}},
#             sort=[("timestamp", 1)]
#         ))
#         return [{"role": m["role"], "content": m["content"]} for m in messages]
#     except Exception as e:
#         print("Failed to load chat history:", e)
#         raise HTTPException(status_code=500, detail="Failed to load history.")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="0.0.0.0", port=8000)










import os
import re
import traceback
from typing import List, Dict
# from pymongo import MongoClient
from dotenv import load_dotenv
from datetime import datetime
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import anthropic
import groq
from utils.email_utils import send_email, format_conversation_for_email
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# === Load environment ===
load_dotenv()
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
MONGO_URI = os.getenv("MONGODB_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

if not GROQ_API_KEY:
    raise ValueError("❌ GROQ_API_KEY missing in .env")
if not MONGO_URI:
    raise ValueError("❌ MONGODB_URI missing in .env")
if not DB_NAME:
    raise ValueError("❌ DB_NAME missing in .env")
if not COLLECTION_NAME:
    raise ValueError("❌ COLLECTION_NAME missing in .env")

# === Clients ===
client_claude = anthropic.Anthropic(api_key=CLAUDE_API_KEY) if CLAUDE_API_KEY else None
client_groq = groq.Groq(api_key=GROQ_API_KEY)

# === MongoDB Setup ===
mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
collection = db[COLLECTION_NAME]

# === Load context ===
CONTEXT_FILE = "Pml_queries.txt"

def load_context(filepath: str, max_chars: int = 3000) -> str:
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            context = f.read()[:max_chars]
            print("Loaded context (first 200 chars):", context[:200])
            return context
    except Exception as e:
        print(f"Failed to load context: {e}")
        return ""

context_text = load_context(CONTEXT_FILE)

# === FastAPI Setup ===
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ✅ Serve React build
# app.mount("/assets", StaticFiles(directory="build/assets"), name="assets")

# @app.get("/{full_path:path}")
# async def serve_react_app(full_path: str):
#     file_path = os.path.join("build", "index.html")
#     if os.path.exists(file_path):
#         return FileResponse(file_path)
#     return {"error": "React build not found"}
app.mount("/assets", StaticFiles(directory="build/assets"), name="assets")

# Serve everything else (SPA fallback)
@app.get("/{path_name:path}")
async def serve_spa(path_name: str):
    file_path = os.path.join("build", "index.html")
    if os.path.exists(file_path):
        return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="Frontend not found")

# === Models ===
class UserInput(BaseModel):
    message: str
    role: str = "user"
    conversation_id: str

class InteractionLog(BaseModel):
    conversation_id: str
    user_name: str
    mobile_number: str
    event_type: str
    metadata: Dict
    timestamp: str

class EmailSummaryRequest(BaseModel):
    conversation_id: str
    recipient: str = "accounts2@paulfincap.com"

# === Core Logic ===

def save_message(conversation_id: str, role: str, content: str):
    collection.insert_one({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow()
    })

def load_conversation(conversation_id: str) -> List[Dict[str, str]]:
    try:
        messages = list(collection.find(
            {"conversation_id": conversation_id, "role": {"$exists": True}, "content": {"$exists": True}},
            sort=[("timestamp", 1)]
        ))
        return [{"role": m["role"], "content": m["content"]} for m in messages]
    except Exception as e:
        print(f"[ERROR] Failed to load conversation from MongoDB: {e}")
        return []

# === Summarization ===
async def summarize_messages(messages: List[Dict[str, str]]) -> str:
    try:
        chat_prompt = "".join([f"{m['role'].capitalize()}: {m['content']}\n" for m in messages])
        if client_claude:
            msg = client_claude.messages.create(
                model="claude-3-opus-20240229",
                max_tokens=200,
                temperature=0.3,
                messages=[{ "role": "user", "content": f"Summarize this chat into exactly 3 short and simple bullet points. Be concise and user-friendly.\n{chat_prompt}" }]
            )
            # reply = msg.content[0].text.strip()
            reply = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', reply)
            print("🤖 PaulBot Reply:\n", reply)
            return reply
    except Exception as e:
        print(f"⚠️ Summarization failed: {e}")
    return "[Summary unavailable]"

@app.get("/")
def read_root():
    return {"message": "Welcome to PaulBot (Claude/Groq). Use POST /chat/ to talk."}

@app.post("/chat/")
async def chat(input: UserInput):
    try:
        if input.message.lower().strip() == "others":
            new_id = str(datetime.utcnow().timestamp()).replace('.', '')
            return { "response": "Sure! How can I help you 😎?", "conversation_id": new_id }

        print(f"[DEBUG] Loading conversation ID: {input.conversation_id}")
        full_history = load_conversation(input.conversation_id)

        if not any(m["role"] == "system" for m in full_history):
            full_history.insert(0, {
                "role": "system",
                "content": f"You are PaulBot — a helpful assistant. Use this context:\n\n{context_text}"
            })

        full_history.append({ "role": input.role, "content": input.message })

        total_chars = sum(len(m["content"]) for m in full_history)

        # prompt_intro = (
        #     "You are PaulBot — a helpful assistant for Paul Merchants customers.\n"
        #     "Always use very short, clear language.\n"
        #     "When explaining, use 2 or 3 bullet points and format section headings/labels with HTML <b>bold</b> tags. Never use **stars** for bold.\n"
        #     "Avoid long paragraphs unless the user explicitly asks for detailed information.\n"
        #     "Make it easy for any customer to quickly understand.\n\n"
        # )
        prompt_intro = (
            "You are PaulBot, a helpful AI assistant for Paul Merchants customers.\n"
            "Your primary goal is to provide short, clear, and easy-to-read answers.\n\n"
            "**MANDATORY RESPONSE FORMATTING - FOLLOW THESE RULES ALWAYS:**\n"
            "1.  **BE CONCISE:** Keep your entire response very short. Use simple, direct language.\n"
            "2.  **USE BULLETS (`•`):** For any list of items or steps, YOU MUST use the bullet character (`•`). Never use asterisks (`*`) or numbers (`1.`).\n"
            "3.  **USE HTML BOLD (`<b>`):** To emphasize keywords, YOU MUST use HTML `<b>` tags. Example: `<b>PML Holidays</b>`. NEVER use markdown `**`.\n"
            "4.  **NO LONG PARAGRAPHS:** If not using a list, each paragraph must be 2 sentences or less (under 25 words total).\n\n"
            "**EXAMPLE OF A PERFECT RESPONSE:**\n"
            "Here are the forex services we offer:\n"
            "• You can <b>buy or sell</b> foreign currency at our branches.\n"
            "• We also help you <b>send money</b> abroad securely.\n\n"
            "Failure to follow these formatting rules will result in an incorrect response. Adhere strictly to this format."
        )


        if total_chars > 12000:
            summary = await summarize_messages(full_history[:-10])
            prompt = prompt_intro + f"Summary of previous conversation:\n{summary}\n\nRecent messages:\n"
            for msg in full_history[-10:]:
                prompt += f"{msg['role'].capitalize()}: {msg['content']}\n"
        else:
            prompt = prompt_intro + "".join([f"{m['role'].capitalize()}: {m['content']}\n" for m in full_history])

        reply = None
        if client_claude:
            try:
                msg = client_claude.messages.create(
                    model="claude-3-opus-20240229",
                    max_tokens=600,
                    temperature=0.7,
                    messages=[{ "role": "user", "content": prompt }]
                )
                reply = msg.content[0].text.strip()
            except Exception as e:
                print("⚠️ Claude failed, switching to Groq. Error:", e)

        if not reply:
            try:
                response = client_groq.chat.completions.create(
                    # model="llama3-70b-8192",
                    # model = "llama-3.1-70b-versatile",
                    model="groq/compound",
                    messages=[{ "role": "user", "content": prompt }],
                    max_tokens=600,
                    temperature=0.7
                )
                reply = response.choices[0].message.content.strip()
            except Exception as e:
                print("❌ Groq call failed:", e)
                raise HTTPException(status_code=500, detail="Both Claude and Groq failed.")

        save_message(input.conversation_id, input.role, input.message)
        save_message(input.conversation_id, "assistant", reply)

        # ✅ Email trigger based on PaulBot message
        # trigger_phrases = [
        #     "If you don't see what you're looking for, click on your preferred choice and explore more options on our website: PML Holidays Website. Our team will connect with you shortly to curate the perfect trip for you!",
        #     "Thank you! We will contact you shortly."
        # ]

        # if any(trigger_phrase.lower() in reply.lower() for trigger_phrase in trigger_phrases):
        messages = list(collection.find(
            {"conversation_id": input.conversation_id},
            sort=[("timestamp", 1)]
        ))
        email_html, df = format_conversation_for_email(messages)
        send_email(
            subject=f"PaulBot Chat Summary - ID: {input.conversation_id}",
            html_content=email_html,
            recipient="accounts2@paulfincap.com"
        )

        return {"response": reply, "conversation_id": input.conversation_id}

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Unhandled server error: {str(e)}")

@app.post("/send-email/")
def trigger_email(conversation_id: str = Query(...), recipient: str = Query(...)):
    messages = list(collection.find({"conversation_id": conversation_id}))
    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    email_html, df = format_conversation_for_email(messages)
    send_email(
        subject=f"PaulBot Chat Summary - ID: {conversation_id}",
        html_content=email_html,
        recipient=recipient
    )
    return {"status": "Email sent"}

@app.post("/send-email-summary/")
async def send_summary(data: EmailSummaryRequest):
    try:
        messages = list(collection.find(
            {"conversation_id": data.conversation_id},
            sort=[("timestamp", 1)]
        ))
        if not messages:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        email_html, df = format_conversation_for_email(messages)
        print("📊 DataFrame Preview:")
        print(df)       
        send_email(
            subject=f"PaulBot Conversation Summary - ID: {data.conversation_id}",
            html_content=email_html,
            recipient=data.recipient
        )
        return {"status": "Email summary sent"}
    
    except Exception as e:
        print("Error sending email summary:", e)
        raise HTTPException(status_code=500, detail="Error sending summary email")


@app.post("/log-interaction/")
async def log_interaction(data: InteractionLog):
    try:
        collection.insert_one({
            "type": "interaction",
            "conversation_id": data.conversation_id,
            "user_name": data.user_name,
            "mobile_number": data.mobile_number,
            "event_type": data.event_type,
            "metadata": data.metadata,
            "timestamp": data.timestamp
        })
        return {"status": "ok"}
    except Exception as e:
        print("Error saving interaction log:", e)
        raise HTTPException(status_code=500, detail="Logging failed")

@app.get("/chat-history/{conversation_id}")
def get_chat_history(conversation_id: str):
    try:
        messages = list(collection.find(
            {"conversation_id": conversation_id, "type": {"$ne": "interaction"}},
            sort=[("timestamp", 1)]
        ))
        return [{"role": m["role"], "content": m["content"]} for m in messages]
    except Exception as e:
        print("Failed to load chat history:", e)
        raise HTTPException(status_code=500, detail="Failed to load history.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4047)