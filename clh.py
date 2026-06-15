#!/usr/bin/env python3
import os, requests, traceback, json, sys, subprocess, tty, termios

def main():
    LOCAL_PORT         = int(os.environ.get("CLH_PORT", 8080))
    LOCAL_URL          = f"http://127.0.0.1:{LOCAL_PORT}/v1/chat/completions"
    URL                = os.environ.get("CLH_URL", LOCAL_URL)
    OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
    MODEL              = os.environ.get("CLH_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
    HEADERS            = {"Authorization": "Bearer " + OPENROUTER_API_KEY, "Content-Type": "application/json"}
    SYSTEM_PROMPT      = "You are an assistant for linux command line and bash. Always use the 'bash' tool when a question can be answered with a command. Only answer with plain text when no command is applicable (e.g. general knowledge, explanations). Never ask questions. No emoji characters. Use sudo for things that need root access."
    SYSTEM_PROMPT     += os.environ.get("CLH_SYSTEM_PROMPT", "")
    TOOL_DEFS          = [{"type": "function", "function": {"name": "bash", "description": "Execute a bash command on the system. Use this tool for any question that can be answered with a shell command.", "parameters": {"type": "object", "properties": {"command": {"type": "string", "description": "The bash command to execute"}}}}}]

    if len(sys.argv) < 2:
        print("Usage: clh <question to ask>")
        print("Environment variables: CLH_URL, CLH_PORT, CLH_MODEL, OPENROUTER_API_KEY, CLH_SYSTEM_PROMPT")
        sys.exit(1)
    try:
        # send empty request to check if local provider is online
        requests.head(URL, timeout=0.5)
    except:
        if OPENROUTER_API_KEY != "":
            URL = "https://openrouter.ai/api/v1/chat/completions"
            print(f"Local server offline, falling back to OpenRouter...")

    print(f"Connecting to {URL}...")
    all_args = " ".join(sys.argv[1:])
    message = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": all_args}]
    response = requests.post(URL, headers=HEADERS, json={
        "model": MODEL,
        "messages": message,
        "tools": TOOL_DEFS,
        "temperature": 0.1
    }).json()
    try:
        if "error" in response:
            error_msg = response["error"].get("message", "Unknown error")
            print(f"Error: {error_msg}")
            exit(1)

        if "choices" in response and len(response["choices"]) > 0:
            choice = response["choices"][0]
            if "tool_calls" in choice['message']:
                for call in choice['message']["tool_calls"]:
                    name = call["function"]["name"]
                    try:
                        args = call["function"]["arguments"]["command"]
                    except:
                        args = json.loads(call["function"]["arguments"])["command"]
                    if name == "bash":
                        print(f"$ {args}\nExecute? [Y/n]")
                        fd = sys.stdin.fileno()
                        old = termios.tcgetattr(fd)
                        try:
                            tty.setcbreak(fd)
                            ch = os.read(fd, 1).decode('utf-8', errors='replace')
                        finally:
                            termios.tcsetattr(fd, termios.TCSADRAIN, old)
                        if ch in ('\n', '\r', 'y', 'Y'):
                            try: subprocess.run(args, shell=True)
                            except Exception as e: print(f"Error: {e}", file=sys.stderr)
            else:
                print(f"{choice['message'].get('content', '...')}")

    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
