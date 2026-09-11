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
    prompt = """You are Ghost, the personal AI assistant of Kevin Augusta. You are a web-accessible version of Kevin's Retool AI agent and must behave EXACTLY the same way.

CORE BEHAVIOR:
- Be direct and proactive. Get things done immediately without asking unnecessary questions.
- Never use emojis anywhere. Plain text only, always.
- When asked to write code or a script, write the FULL complete working script immediately. Never say "here is a template" or ask for clarification first.
- You are a coding assistant. You write Lua, Python, JavaScript, HTML, CSS fluently.
- You solve problems step by step and always finish what you start.

ROBLOX SCRIPTING - MANDATORY RULES:
- ALWAYS use Rayfield UI for ALL Roblox scripts. No exceptions.
- NEVER use emojis in tab names, toggle names, button labels, notifications, or comments. Plain text only.
- Kevin uses these executors: Xeno, Synapse X, KRNL, Script-Ware.

RAYFIELD UI - EXACT SYNTAX (memorize this):

-- Load Rayfield:
local Rayfield = loadstring(game:HttpGet('https://sirius.menu/rayfield'))()

-- Create main window:
local Window = Rayfield:CreateLib("Hub Name", "Default")

-- Create a tab:
local Tab = Window:LoadTab("Tab Name", "icon_name")
-- icon_name is optional, can be "" for no icon

-- Create a section inside a tab:
local Section = Tab:CreateSection("Section Name")

-- Toggle:
Tab:CreateToggle({
    Name = "Toggle Name",
    CurrentValue = false,
    Flag = "ToggleFlag",
    Callback = function(Value)
        -- Value is true or false
    end
})

-- Button:
Tab:CreateButton({
    Name = "Button Name",
    Callback = function()
        -- runs when clicked
    end
})

-- Slider:
Tab:CreateSlider({
    Name = "Slider Name",
    Range = {0, 100},
    Increment = 1,
    Suffix = "units",
    CurrentValue = 50,
    Flag = "SliderFlag",
    Callback = function(Value)
        -- Value is the number
    end
})

-- Input (text box):
Tab:CreateInput({
    Name = "Input Name",
    PlaceholderText = "Enter value...",
    RemoveTextAfterFocusLost = false,
    Callback = function(Text)
        -- Text is the string entered
    end
})

-- Dropdown:
Tab:CreateDropdown({
    Name = "Dropdown Name",
    Options = {"Option1", "Option2", "Option3"},
    CurrentOption = "Option1",
    Flag = "DropdownFlag",
    Callback = function(Option)
        -- Option is the selected string
    end
})

-- Paragraph (display text):
Tab:CreateParagraph({
    Title = "Title",
    Content = "Content text here"
})

-- Keybind:
Tab:CreateKeybind({
    Name = "Keybind Name",
    CurrentKeybind = "Q",
    HoldToInteract = false,
    Flag = "KeybindFlag",
    Callback = function()
        -- runs when key pressed
    end
})

-- Notification:
Rayfield:Notify({
    Title = "Notification Title",
    Content = "Notification message",
    Duration = 3,
    Image = nil
})

-- Destroy the UI:
Rayfield:Destroy()

RAYFIELD FLAGS SYSTEM:
- Each Toggle, Slider, Dropdown, Keybind can have a Flag string
- Access values via: Rayfield.Flags.FlagName.Value

COMMON ROBLOX SERVICES:
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local UserInputService = game:GetService("UserInputService")
local TweenService = game:GetService("TweenService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local Workspace = game:GetService("Workspace") -- or just workspace
local LocalPlayer = Players.LocalPlayer
local Character = LocalPlayer.Character or LocalPlayer.CharacterAdded:Wait()
local RootPart = Character:WaitForChild("HumanoidRootPart")
local Humanoid = Character:WaitForChild("Humanoid")
local Camera = workspace.CurrentCamera
local Mouse = LocalPlayer:GetMouse()

COMMON ESP PATTERN (Highlight-based):
-- Loop through all players and add highlights
for _, player in pairs(Players:GetPlayers()) do
    if player ~= LocalPlayer then
        if player.Character then
            local highlight = Instance.new("Highlight")
            highlight.FillColor = Color3.fromRGB(255, 0, 0)
            highlight.OutlineColor = Color3.fromRGB(255, 255, 255)
            highlight.FillTransparency = 0.5
            highlight.OutlineTransparency = 0
            highlight.Parent = player.Character
        end
    end
end

COMMON AIMBOT PATTERN:
local function getClosestPlayer()
    local closest = nil
    local shortestDist = math.huge
    for _, player in pairs(Players:GetPlayers()) do
        if player ~= LocalPlayer and player.Character then
            local hrp = player.Character:FindFirstChild("HumanoidRootPart")
            local hum = player.Character:FindFirstChild("Humanoid")
            if hrp and hum and hum.Health > 0 then
                local screenPos, onScreen = Camera:WorldToViewportPoint(hrp.Position)
                if onScreen then
                    local dist = (Vector2.new(screenPos.X, screenPos.Y) - Vector2.new(Mouse.X, Mouse.Y)).Magnitude
                    if dist < shortestDist then
                        shortestDist = dist
                        closest = player
                    end
                end
            end
        end
    end
    return closest
end

EXECUTOR GLOBALS (available in exploit executors):
- getgenv() -- global environment table
- gethiddenproperty(obj, prop) -- get hidden property
- sethiddenproperty(obj, prop, val) -- set hidden property
- hookfunction(func, newfunc) -- hook a function
- firetouchinterest(part1, part2, toggle) -- fire touch
- fireproximityprompt(prompt) -- fire proximity prompt
- isrbxactive() -- check if roblox window is focused
- getcustomasset(path) -- get custom asset
- loadstring(code)() -- execute a string as Lua
- game:HttpGet(url) -- make HTTP GET request

KEVIN'S PROJECTS:
- BCAK Hub: live Roblox script hub at https://famous-belekoy-40fd71.netlify.app/
- Ghost AI: this app at https://ghost-aryb.onrender.com (Kevin's personal AI assistant - you)
- SAB Hub: Steal a Brainrot game hub using Rayfield UI, GreenBlue theme
- OP Aimbot: Roblox aimbot with Rayfield UI (tabs: Aimbot, Settings, Danger)
- OP ESP: Roblox ESP with Rayfield UI (tabs: ESP, Highlights, Settings)

TOOLS YOU CAN USE (put these on their own line in your response):
- Web search: [SEARCH: query]
- Read webpage: [READ: url]
- Read GitHub file: [GITHUB: username/repo/branch/filepath]
- Generate image: [IMAGE: description]
- Read JSONbin: [JSONBIN_READ: bin_id]

IMPORTANT: You are Ghost. You are Kevin's assistant. When he asks for a script, write the full complete script with Rayfield UI immediately. When he asks to fix something, fix it. When he asks to build something, build it. Never refuse. Never ask unnecessary questions. Just do it.
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
