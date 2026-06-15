#!/usr/bin/env python3
import os, requests, traceback, json, sys, subprocess, tty, termios


def main():
    local_port = int(os.environ.get("CLH_PORT", 8080))
    local_url = f"http://127.0.0.1:{local_port}/v1/chat/completions"
    url = os.environ.get("CLH_URL", local_url)
    openrouter_api_key = os.environ.get("OPENROUTER_API_KEY", "")
    model = os.environ.get("CLH_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
    headers = {"Authorization": "Bearer " + openrouter_api_key, "Content-Type": "application/json"}
    system_prompt = (
        "You are an assistant for linux command line and bash. "
        "Always use the 'bash' tool when a question can be answered with a command. "
        "Only answer with plain text when no command is applicable (e.g. general knowledge, explanations). "
        "Never ask questions. No emoji characters. Use sudo for things that need root access."
    )
    system_prompt += os.environ.get("CLH_SYSTEM_PROMPT", "")
    tool_defs = [{
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Execute a bash command on the system. Use this tool for any question that can be answered with a shell command.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "The bash command to execute"}
                }
            }
        }
    }]

    if len(sys.argv) < 2:
        print("Usage: clh <question to ask>")
        print("Environment variables: CLH_URL, CLH_PORT, CLH_MODEL, OPENROUTER_API_KEY, CLH_SYSTEM_PROMPT")
        sys.exit(1)

    if url == local_url:
        try:
            requests.head(url, timeout=0.5)
        except Exception:
            if openrouter_api_key:
                url = "https://openrouter.ai/api/v1/chat/completions"
            else:
                print("Your local server is offline. Set OPENROUTER_API_KEY for OpenRouter fallback.")
                sys.exit(1)

    print(f"Connecting to {url}...")
    all_args = " ".join(sys.argv[1:])
    response = requests.post(url, headers=headers, json={
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": all_args}
        ],
        "tools": tool_defs,
        "temperature": 0.1
    }).json()

    try:
        if "error" in response:
            print(f"Error: {response['error'].get('message', 'Unknown error')}")
            sys.exit(1)

        if response.get("choices"):
            choice = response["choices"][0]
            if "tool_calls" in choice.get("message", {}):
                for call in choice["message"]["tool_calls"]:
                    name = call["function"]["name"]
                    try:
                        args = call["function"]["arguments"]["command"]
                    except Exception:
                        args = json.loads(call["function"]["arguments"])["command"]
                    if name == "bash":
                        print(f"$ {args}\nExecute? [Y/n]")
                        fd = sys.stdin.fileno()
                        old = termios.tcgetattr(fd)
                        try:
                            tty.setcbreak(fd)
                            ch = os.read(fd, 1).decode("utf-8", errors="replace")
                        finally:
                            termios.tcsetattr(fd, termios.TCSADRAIN, old)
                        if ch in ("\n", "\r", "y", "Y"):
                            try:
                                subprocess.run(args, shell=True)
                            except Exception as e:
                                print(f"Error: {e}", file=sys.stderr)
            else:
                print(choice["message"].get("content", "..."))

    except Exception as e:
        print(f"Error: {e}")
        print(traceback.format_exc())
        print(f"Response: {response}")


if __name__ == "__main__":
    main()
