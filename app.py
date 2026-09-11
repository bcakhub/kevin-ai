import os
import json
import requests
from flask import Flask, render_template, request, session, redirect, url_for, Response, stream_with_context, jsonify
from bs4 import BeautifulSoup
from groq import Groq

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "ghost-secret")

APP_PASSWORD = os.environ.get("APP_PASSWORD", "iloveubatcat")
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
JSONBIN_KEY = os.environ.get("JSONBIN_KEY", "")
JSONBIN_BIN_ID = os.environ.get("JSONBIN_BIN_ID", "")
CHAT_HISTORY_BIN_ID = "6aa318f2ffd5d16053f7c8f5"
GROQ_MODEL = "openai/gpt-oss-120b"

client = Groq(api_key=GROQ_API_KEY)

JSONBIN_HEADERS = {
    "X-Master-Key": JSONBIN_KEY,
    "Content-Type": "application/json"
}

def read_memory():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}/latest", headers=JSONBIN_HEADERS, timeout=5)
        return r.json().get("record", {})
    except:
        return {}

def write_memory(data):
    try:
        requests.put(f"https://api.jsonbin.io/v3/b/{JSONBIN_BIN_ID}", headers=JSONBIN_HEADERS, json=data, timeout=5)
    except:
        pass

def read_chat_history():
    try:
        r = requests.get(f"https://api.jsonbin.io/v3/b/{CHAT_HISTORY_BIN_ID}/latest", headers=JSONBIN_HEADERS, timeout=5)
        data = r.json().get("record", {})
        return data.get("chat_history", [])
    except:
        return []

def write_chat_history(history):
    try:
        requests.put(f"https://api.jsonbin.io/v3/b/{CHAT_HISTORY_BIN_ID}", headers=JSONBIN_HEADERS, json={"chat_history": history}, timeout=5)
    except:
        pass

def build_system_prompt():
    memory = read_memory()

    prompt = """You are Ghost, the personal AI assistant of Kevin Augusta. You are a web-accessible version of Kevin's Retool AI agent - you must behave EXACTLY the same way.

CORE BEHAVIOR:
- Be direct and proactive. Get things done immediately without asking unnecessary questions.
- Never use emojis anywhere. Plain text only, always.
- When asked to write code or a script, write the FULL complete script immediately. Never say "here is a template" or ask for clarification first.
- You are a coding assistant. You write Lua, Python, JavaScript, HTML, CSS, and any other language fluently.
- You solve problems step by step and always finish what you start.
- You remember Kevin's past projects and preferences.

ROBLOX SCRIPTING RULES (very important):
- ALWAYS use Rayfield UI for ALL Roblox scripts. No exceptions.
- Load Rayfield like this: local Rayfield = loadstring(game:HttpGet('https://sirius.menu/rayfield'))()
- NEVER use emojis in script tab names, toggle names, button labels, notifications, or comments.
- Plain text only in all scripts.
- Kevin uses these executors: Xeno, Synapse X, KRNL, Script-Ware.
- Write scripts that work on all major executors unless specified otherwise.
- Rayfield UI structure: CreateLib (window) -> LoadTab (tab) -> CreateToggle / CreateButton / CreateSlider / CreateInput / CreateDropdown etc.

KEVIN'S PROJECTS:
- BCAK Hub: live Roblox script hub website at https://famous-belekoy-40fd71.netlify.app/
- Ghost AI: this app - live at https://ghost-aryb.onrender.com - Kevin's personal AI assistant (you)
- SAB Hub: Steal a Brainrot Roblox game hub using Rayfield UI, GreenBlue theme
- OP Aimbot: Roblox aimbot script using Rayfield UI with tabs: Aimbot, Settings, Danger
- OP ESP: Roblox ESP script using Rayfield UI with tabs: ESP, Highlights, Settings

KEVIN'S PREFERENCES:
- UI Library: Rayfield UI (for all Roblox scripts)
- No emojis anywhere, ever
- Plain text only
- Executors: Xeno, Synapse X, KRNL, Script-Ware

CODING STYLE:
- Write complete, working, copy-paste ready code every time
- Include comments in plain text (no emojis in comments)
- For Roblox scripts, always include proper Rayfield window creation, tabs, and elements
- For Python/Flask, write production-ready code
- For HTML/CSS, write clean modern code

TOOLS YOU CAN USE (include in your response):
- Web search: [SEARCH: query]
- Read webpage: [READ: url]
- Read GitHub file: [GITHUB: username/repo/branch/filepath]
- Generate image: [IMAGE: description]
- Read JSONbin: [JSONBIN_READ: bin_id]

IMPORTANT: You are Ghost. You are Kevin's assistant. When he asks you to make a script, make it. When he asks you to fix something, fix it. When he asks you to build something, build it. Do not ask unnecessary questions. Just do it.
"""
    return prompt

def process_tools(text):
    lines = text.split("\n")
    output_lines = []
    for line in lines:
        if "[SEARCH:" in line:
            query = line.split("[SEARCH:")[1].split("]")[0].strip()
            try:
                r = requests.get(f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json&no_html=1", timeout=5)
                data = r.json()
                abstract = data.get("AbstractText", "") or data.get("Answer", "") or "No results found."
                output_lines.append(f"[Search result for '{query}']: {abstract}")
            except:
                output_lines.append(f"[Search failed for '{query}']")
        elif "[READ:" in line:
            url = line.split("[READ:")[1].split("]")[0].strip()
            try:
                r = requests.get(url, timeout=5)
                soup = BeautifulSoup(r.text, "html.parser")
                text_content = soup.get_text()[:2000]
                output_lines.append(f"[Page content from {url}]: {text_content}")
            except:
                output_lines.append(f"[Failed to read {url}]")
        elif "[GITHUB:" in line:
            parts = line.split("[GITHUB:")[1].split("]")[0].strip().split("/")
            if len(parts) >= 4:
                gh_user, gh_repo, gh_branch = parts[0], parts[1], parts[2]
                gh_path = "/".join(parts[3:])
                try:
                    r = requests.get(f"https://raw.githubusercontent.com/{gh_user}/{gh_repo}/{gh_branch}/{gh_path}", timeout=5)
                    output_lines.append(f"[GitHub file {gh_path}]: {r.text[:2000]}")
                except:
                    output_lines.append(f"[Failed to read GitHub file]")
        elif "[IMAGE:" in line:
            desc = line.split("[IMAGE:")[1].split("]")[0].strip()
            encoded = requests.utils.quote(desc)
            output_lines.append(f"[Image generated]: https://image.pollinations.ai/prompt/{encoded}")
        elif "[JSONBIN_READ:" in line:
            bin_id = line.split("[JSONBIN_READ:")[1].split("]")[0].strip()
            try:
                r = requests.get(f"https://api.jsonbin.io/v3/b/{bin_id}/latest", headers=JSONBIN_HEADERS, timeout=5)
                output_lines.append(f"[JSONbin data]: {json.dumps(r.json().get('record', {}))[:1000]}")
            except:
                output_lines.append("[Failed to read JSONbin]")
        else:
            output_lines.append(line)
    return "\n".join(output_lines)

@app.route("/")
def index():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if password == APP_PASSWORD:
            session["logged_in"] = True
            session["chat_history"] = read_chat_history()
            return redirect(url_for("index"))
        else:
            error = "Wrong password."
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/history")
def history():
    if "logged_in" not in session:
        return jsonify([])
    return jsonify(session.get("chat_history", []))

@app.route("/memory")
def memory_page():
    if "logged_in" not in session:
        return redirect(url_for("login"))
    return render_template("memory.html")

@app.route("/memory/read")
def memory_read():
    data = read_memory()
    return jsonify(data)

@app.route("/memory/write", methods=["POST"])
def memory_write():
    data = request.json
    write_memory(data)
    return jsonify({"success": True})

@app.route("/chat", methods=["POST"])
def chat():
    if "logged_in" not in session:
        return jsonify({"error": "Not logged in"}), 401

    user_message = request.form.get("message", "")
    file_content = ""

    if "file" in request.files:
        f = request.files["file"]
        try:
            file_content = f.read().decode("utf-8")
            user_message += f"\n\n[File uploaded: {f.filename}]\n{file_content[:3000]}"
        except:
            pass

    if not user_message.strip():
        return jsonify({"error": "Empty message"}), 400

    history = session.get("chat_history", [])
    history.append({"role": "user", "content": user_message})

    system_prompt = build_system_prompt()

    messages = [{"role": "system", "content": system_prompt}]
    for msg in history[-60:]:
        messages.append(msg)

    def generate():
        full_response = ""
        try:
            stream = client.chat.completions.create(
                model=GROQ_MODEL,
                messages=messages,
                stream=True,
                max_tokens=8192
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_response += delta
                yield f"data: {json.dumps({'token': delta})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'token': f'Error: {str(e)}'})}\n\n"

        processed = process_tools(full_response)
        if processed != full_response:
            yield f"data: {json.dumps({'tool_result': processed})}\n\n"

        history.append({"role": "assistant", "content": full_response})
        session["chat_history"] = history
        write_chat_history(history[-60:])
        yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(stream_with_context(generate()), mimetype="text/event-stream")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
