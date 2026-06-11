# Mac Local Model Runtime Notes

## Ollama
Best for local chat, embedding, and OpenAI-compatible workflows with minimal setup. Lists only models stored in `~/.ollama/models`; it does not manage Hugging Face cache.

## Hugging Face cache
Default hub cache is `~/.cache/huggingface/hub`. Use `hf cache ls` to inspect. Cached repos are not necessarily runnable without the correct runtime.

## MLX Whisper
Best first choice for Apple Silicon speech-to-text. Prefer `mlx-community/whisper-large-v3-turbo` for fast local transcription and `whisper-large-v3` when accuracy matters more than latency.

## whisper.cpp
Good C/C++ path for portable local Whisper and Metal acceleration. Useful when the user wants a standalone binary or GGML/GGUF-style model files.

## LM Studio
Good GUI for browsing/downloading/running GGUF LLMs and exposing a local OpenAI-compatible server. It does not automatically replace Ollama or Hugging Face cache management.
