# clh - Command Line Helper by abmt-community

CLI tool for asking LLMs questions and executing suggested bash commands with confirmation. Ask what you need, review the command, and run it only if you approve. Useful for discovering commands you don't know, automating repetitive shell tasks, or getting interactive help without leaving the terminal.

```
$ clh "what is my ip address"
Connecting to http://127.0.0.1:8080/v1/chat/completions...
$ hostname -I
Execute? [Y/n]
192.168.1.10
```

This project shows in less than 80 lines how to connect to a LLM API and use tool calling.

## Installation

```bash
curl -L https://raw.githubusercontent.com/abmt-community/clh/master/clh.py -o clh.py
chmod +x clh.py
sudo mv clh.py /usr/local/bin/clh
```

Or for user-only use:

```bash
mkdir -p ~/.local/bin
curl -L https://raw.githubusercontent.com/abmt-community/clh/master/clh.py -o ~/.local/bin/clh
chmod +x ~/.local/bin/clh
```

## Usage

```bash
clh "How do I list all running docker containers?"
```

## Configuration

Environment variables:

| Variable | Default | Description |
|---|---|---|
| `CLH_URL` | `http://127.0.0.1:8080/v1/chat/completions` | Inference API endpoint |
| `CLH_PORT` | `8080` | Local server port (only used if `CLH_URL` is not set) |
| `CLH_MODEL` | `nvidia/nemotron-3-nano-30b-a3b:free` | Model to use |
| `OPENROUTER_API_KEY` | *(empty)* | API key for OpenRouter fallback |
| `CLH_SYSTEM_PROMPT` | *(empty)* | Additional system prompt appended to the default |

### Fallback

When no custom `CLH_URL` is set, clh tries to connect to a local LLM server at `127.0.0.1:8080`. It sends a quick HEAD request to check if the server is reachable:

- **Local server available** — uses it for inference.
- **Local server offline + `OPENROUTER_API_KEY` set** — falls back to OpenRouter (`https://openrouter.ai/api/v1/chat/completions`).
- **Local server offline + no API key** — prints an error and exits.

## Requirements

- Python 3.7+
- `requests` (install with `pip install requests`)

## License

MIT
