---
name: local-model-orchestrator
description: Scan, explain, select, install, and call local AI models across Ollama, Hugging Face cache, MLX Whisper, whisper.cpp, LM Studio, and common Mac model stores. Use when the user asks to list local models, understand what installed models do, check whether models are healthy, manage local model caches, choose a local model for a task, run local inference/transcription/embedding, or prefer Apple Silicon / Mac-optimized models.
---

# Local Model Orchestrator

## Core Workflow

1. Scan before advising or calling models:
   ```bash
   python3 /Users/apple/.agents/skills/local-model-orchestrator/scripts/local_model_manager.py scan --format table
   ```
2. Explain each model by provider, purpose, status, size, and call method. Use the script's purpose labels as the starting point, then add task-specific judgment.
3. Choose a model/runtime by task:
   - **Chat, reasoning, coding, summarization**: prefer Ollama models or an OpenAI-compatible local endpoint already running.
   - **Embeddings / RAG**: prefer Ollama embedding models such as `nomic-embed-text`, `mxbai-embed-large`, `bge-m3`, or `qwen3-embedding` if installed.
   - **Speech-to-text / transcription**: prefer `mlx-whisper` on Apple Silicon; use `whisper-large-v3-turbo` for speed, `whisper-large-v3` for accuracy, smaller Whisper models for lightweight use.
   - **Raw GGUF files**: use llama.cpp / LM Studio / Ollama import only if an actual GGUF file exists.
   - **Hugging Face cache**: treat as cached assets, not necessarily runnable unless the matching runtime is installed.
4. If the task has a Mac-optimized model path, recommend that path before generic alternatives. Do not install without explicit user consent.
5. When calling a model, run the smallest deterministic probe first, then the real task.

## Scanning

Use:

```bash
python3 /Users/apple/.agents/skills/local-model-orchestrator/scripts/local_model_manager.py scan --format table
python3 /Users/apple/.agents/skills/local-model-orchestrator/scripts/local_model_manager.py scan --format json
```

The scanner covers:
- Ollama models via `ollama list` and `ollama show`.
- Hugging Face cache via `hf cache ls --format json` or direct cache directory inspection.
- Common local model files: `.gguf`, `.safetensors`, `.bin`, `.onnx`, `.mlpackage`, `.npz`.
- Common Mac app stores: LM Studio, Jan, GPT4All, MLX/HF cache, Ollama.

Report health conservatively:
- `ok`: listed by the owning runtime or present with expected files.
- `found`: raw model file exists but no runtime test was performed.
- `missing-runtime`: model/cache exists but the recommended runtime command is missing.
- `unknown`: not enough information; do not claim it is runnable.

## Calling Models

Use the script helpers when possible:

```bash
python3 /Users/apple/.agents/skills/local-model-orchestrator/scripts/local_model_manager.py call-ollama MODEL "prompt"
python3 /Users/apple/.agents/skills/local-model-orchestrator/scripts/local_model_manager.py transcribe AUDIO_PATH --model mlx-community/whisper-large-v3-turbo
```

For Ollama, first verify the model exists:

```bash
ollama list
ollama show MODEL
```

Then call:

```bash
ollama run MODEL "prompt"
```

For MLX Whisper, verify/install with user consent:

```bash
command -v mlx_whisper || python3 -m pip install mlx-whisper
mlx_whisper audio.mp3 --model mlx-community/whisper-large-v3-turbo
```

For Hugging Face cache, use:

```bash
hf cache ls
hf cache ls --revisions
```

Do not assume a Hugging Face cached model can be called directly. Match it to a runtime first.

## Apple Silicon Recommendation Rules

Prefer Apple Silicon optimized models/runtimes when all are true:
- The user is on macOS arm64 or Apple Silicon is likely from context.
- The task has a known MLX/Core ML/Metal-accelerated path.
- The model is not already installed in a more suitable local runtime.

Common recommendations:
- **Speech-to-text**: `mlx-whisper` + `mlx-community/whisper-large-v3-turbo`; choose `large-v3` if accuracy matters more than speed.
- **Local LLM chat**: Ollama for ergonomics; LM Studio for GUI/model browsing; MLX runtimes for maximum Apple Silicon performance when the user accepts more setup.
- **Embedding**: Ollama `nomic-embed-text` is a good default if already installed; `mxbai-embed-large` / `bge-m3` / `qwen3-embedding` when multilingual or retrieval quality matters.

When recommending an install, include the command and explain why, but ask before downloading large models or installing new packages.

## Output Contract

When the user asks to scan/manage local models, return:
- Total count by ecosystem.
- Table with `Name`, `Provider`, `Purpose`, `Size`, `Status`, `Call method`.
- Any likely duplicates or stale caches.
- Recommended model for the user's current task.
- Exact next command to run.

Keep secrets out of output. Never print API keys found in local config.
