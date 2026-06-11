#!/usr/bin/env python3
"""Scan and call local AI models across common Mac runtimes.

Safe by default: scan/read/call only. No deletes or downloads.
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

HOME = Path.home()


@dataclass
class ModelItem:
    provider: str
    name: str
    purpose: str
    size: str
    status: str
    call_method: str
    path: str = ""
    notes: str = ""


def run(cmd: list[str], timeout: int = 20) -> tuple[int, str, str]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return p.returncode, p.stdout, p.stderr
    except FileNotFoundError as e:
        return 127, "", str(e)
    except subprocess.TimeoutExpired as e:
        return 124, e.stdout or "", e.stderr or "timeout"


def human_size(path: Path) -> str:
    try:
        size = path.stat().st_size if path.is_file() else sum(f.stat().st_size for f in path.rglob("*") if f.is_file())
    except Exception:
        return "?"
    units = ["B", "KB", "MB", "GB", "TB"]
    n = float(size)
    for unit in units:
        if n < 1024 or unit == units[-1]:
            return f"{n:.1f}{unit}" if unit != "B" else f"{int(n)}B"
        n /= 1024
    return "?"


def infer_purpose(name: str, path: str = "") -> str:
    text = f"{name} {path}".lower()
    if any(x in text for x in ["whisper", "asr", "speech", "transcrib"]):
        return "speech-to-text/asr"
    if any(x in text for x in ["embed", "embedding", "bge", "e5", "minilm", "nomic"]):
        return "embedding/rag"
    if any(x in text for x in ["llava", "vision", "vl", "ocr"]):
        return "vision/ocr"
    if any(x in text for x in ["coder", "code", "qwen", "deepseek", "llama", "mistral", "gemma", "phi"]):
        return "chat/code/llm"
    return "model/cache"


def scan_ollama() -> list[ModelItem]:
    if not shutil.which("ollama"):
        return []
    code, out, _ = run(["ollama", "list"])
    if code != 0:
        return []
    items: list[ModelItem] = []
    for line in out.splitlines()[1:]:
        parts = line.split()
        if len(parts) < 3:
            continue
        name = parts[0]
        size = " ".join(parts[2:4]) if len(parts) >= 4 else parts[2]
        ok, _, _ = run(["ollama", "show", name], timeout=10)
        items.append(ModelItem(
            provider="Ollama",
            name=name,
            purpose=infer_purpose(name),
            size=size,
            status="ok" if ok == 0 else "unknown",
            call_method=f"ollama run {name} 'prompt'" if "embed" not in name.lower() else f"ollama embeddings -m {name} -p 'text'",
            path=str(HOME / ".ollama" / "models"),
        ))
    return items


def scan_hf() -> list[ModelItem]:
    items: list[ModelItem] = []
    hf = shutil.which("hf")
    if hf:
        code, out, _ = run([hf, "cache", "ls", "--format", "json"], timeout=30)
        if code == 0 and out.strip():
            try:
                data = json.loads(out)
                repos = data if isinstance(data, list) else data.get("repos") or data.get("entries") or []
                for r in repos:
                    rid = r.get("id") or r.get("repo_id") or r.get("name") or ""
                    if not rid:
                        continue
                    size = str(r.get("size") or r.get("size_on_disk_str") or r.get("size_on_disk") or "?")
                    path = str(r.get("local_path") or r.get("repo_path") or "")
                    items.append(ModelItem(
                        provider="HuggingFace",
                        name=rid,
                        purpose=infer_purpose(rid, path),
                        size=size,
                        status="ok",
                        call_method=recommend_call_method(rid, "HuggingFace"),
                        path=path,
                        notes="cache entry; match to runtime before calling",
                    ))
                return items
            except Exception:
                pass
    hub = HOME / ".cache" / "huggingface" / "hub"
    if hub.exists():
        for p in sorted(hub.glob("models--*")):
            name = p.name.removeprefix("models--").replace("--", "/")
            items.append(ModelItem(
                provider="HuggingFace",
                name=f"model/{name}",
                purpose=infer_purpose(name, str(p)),
                size=human_size(p),
                status="ok" if (p / "snapshots").exists() else "unknown",
                call_method=recommend_call_method(name, "HuggingFace"),
                path=str(p),
                notes="discovered from cache directory",
            ))
    return items


def common_roots() -> list[Path]:
    # Keep this list narrow. Broadly scanning ~/.cache creates false positives from
    # package test fixtures (tiny ONNX/NPZ files) rather than user-installed models.
    roots = [
        HOME / ".cache" / "whisper",
        HOME / ".cache" / "torch",
        HOME / ".cache" / "modelscope",
        HOME / ".lmstudio",
        HOME / "Library" / "Application Support" / "LM Studio",
        HOME / "Library" / "Application Support" / "Jan",
        HOME / "Library" / "Application Support" / "nomic.ai" / "GPT4All",
        HOME / "Models",
    ]
    return [r for r in roots if r.exists()]


def scan_files() -> list[ModelItem]:
    exts = {".gguf", ".safetensors", ".onnx", ".mlpackage", ".npz"}
    items: list[ModelItem] = []
    seen: set[str] = set()
    for root in common_roots():
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in exts:
                continue
            try:
                if p.stat().st_size < 50 * 1024 * 1024:
                    continue
            except Exception:
                continue
            key = str(p.resolve())
            if key in seen:
                continue
            seen.add(key)
            provider = "File"
            if "LM Studio" in str(p) or ".lmstudio" in str(p):
                provider = "LM Studio"
            elif "mlx" in str(p).lower() or p.suffix.lower() == ".npz":
                provider = "MLX/File"
            items.append(ModelItem(
                provider=provider,
                name=p.name,
                purpose=infer_purpose(p.name, str(p)),
                size=human_size(p),
                status="found",
                call_method=recommend_call_method(p.name, provider, p),
                path=str(p),
            ))
    return items


def recommend_call_method(name: str, provider: str, path: Path | None = None) -> str:
    low = name.lower()
    if "whisper" in low:
        if provider == "HuggingFace" and "faster-whisper" in low:
            return "faster-whisper runtime or install mlx-whisper Apple Silicon model"
        return f"mlx_whisper audio.mp3 --model {name.replace('model/', '')}" if provider == "HuggingFace" else "mlx_whisper audio.mp3 --model MODEL_OR_PATH"
    if provider == "Ollama":
        return f"ollama run {name} 'prompt'"
    if path and path.suffix.lower() == ".gguf":
        return f"llama-cli -m '{path}' -p 'prompt'"
    if provider == "LM Studio":
        return "open in LM Studio or serve via local OpenAI-compatible API"
    if provider == "HuggingFace":
        return "use matching runtime; for Whisper prefer mlx-whisper on Apple Silicon"
    return "runtime-specific"


def scan_all() -> list[ModelItem]:
    items = scan_ollama() + scan_hf() + scan_files()
    # De-duplicate obvious HF snapshot files already represented by repo.
    unique: dict[tuple[str, str, str], ModelItem] = {}
    for item in items:
        key = (item.provider, item.name, item.path)
        unique[key] = item
    return list(unique.values())


def print_table(items: list[ModelItem]) -> None:
    print(f"Total local models/caches found: {len(items)}")
    counts: dict[str, int] = {}
    for item in items:
        counts[item.provider] = counts.get(item.provider, 0) + 1
    if counts:
        print("By provider: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    print("-" * 140)
    print(f"{'PROVIDER':14} {'PURPOSE':20} {'SIZE':10} {'STATUS':10} {'NAME':42} CALL METHOD")
    print("-" * 140)
    for item in items:
        name = item.name[:42]
        print(f"{item.provider:14} {item.purpose[:20]:20} {item.size[:10]:10} {item.status[:10]:10} {name:42} {item.call_method}")
        if item.path:
            print(f"{'':14} {'path:':20} {item.path}")
        if item.notes:
            print(f"{'':14} {'note:':20} {item.notes}")


def cmd_scan(args: argparse.Namespace) -> int:
    items = scan_all()
    if args.format == "json":
        print(json.dumps([asdict(x) for x in items], ensure_ascii=False, indent=2))
    else:
        print_table(items)
    if args.recommend:
        print()
        print(recommend_for_task(args.recommend, items))
    return 0


def recommend_for_task(task: str, items: list[ModelItem]) -> str:
    low = task.lower()
    is_apple = platform.system() == "Darwin" and platform.machine() in {"arm64", "aarch64"}
    if any(x in low for x in ["transcribe", "speech", "audio", "whisper", "转写", "语音", "音频", "字幕"]):
        installed = [i for i in items if "whisper" in i.name.lower()]
        if is_apple:
            base = "Recommended: mlx-whisper + mlx-community/whisper-large-v3-turbo for Apple Silicon speech-to-text."
            cmd = "Command: mlx_whisper audio.mp3 --model mlx-community/whisper-large-v3-turbo"
        else:
            base = "Recommended: faster-whisper or whisper.cpp for speech-to-text."
            cmd = "Command: whisper-cli or faster-whisper with a local Whisper model"
        if installed:
            return base + " Installed Whisper-like cache found: " + ", ".join(i.name for i in installed) + ". " + cmd
        return base + " Ask before installing/downloading. " + cmd
    if any(x in low for x in ["embed", "embedding", "rag", "检索", "向量"]):
        embeds = [i for i in items if "embedding" in i.purpose]
        if embeds:
            return "Recommended installed embedding model: " + embeds[0].name + f". Call: {embeds[0].call_method}"
        return "Recommended install: ollama pull nomic-embed-text or ollama pull bge-m3 for multilingual retrieval."
    ollama = [i for i in items if i.provider == "Ollama" and "chat" in i.purpose]
    if ollama:
        return "Recommended installed chat/code model: " + ollama[0].name + f". Call: {ollama[0].call_method}"
    return "No installed chat LLM found. Recommended install for Mac via Ollama: qwen3:8b for general chat, qwen2.5-coder:7b or qwen3-coder if coding, subject to memory and download approval."


def cmd_call_ollama(args: argparse.Namespace) -> int:
    if not shutil.which("ollama"):
        print("ollama command not found", file=sys.stderr)
        return 127
    code, _, err = run(["ollama", "show", args.model], timeout=10)
    if code != 0:
        print(f"Ollama model not available: {args.model}\n{err}", file=sys.stderr)
        return code
    cmd = ["ollama", "run", args.model, args.prompt]
    return subprocess.call(cmd)


def cmd_transcribe(args: argparse.Namespace) -> int:
    exe = shutil.which("mlx_whisper")
    if not exe:
        print("mlx_whisper command not found. Install with: python3 -m pip install mlx-whisper", file=sys.stderr)
        return 127
    cmd = [exe, args.audio, "--model", args.model]
    if args.output_format:
        cmd += ["--format", args.output_format]
    return subprocess.call(cmd)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Scan and call local AI models")
    sub = parser.add_subparsers(dest="cmd", required=True)

    scan = sub.add_parser("scan", help="scan local model stores")
    scan.add_argument("--format", choices=["table", "json"], default="table")
    scan.add_argument("--recommend", help="task description to recommend a model for")
    scan.set_defaults(func=cmd_scan)

    call = sub.add_parser("call-ollama", help="call an installed Ollama model")
    call.add_argument("model")
    call.add_argument("prompt")
    call.set_defaults(func=cmd_call_ollama)

    tr = sub.add_parser("transcribe", help="transcribe audio via mlx-whisper")
    tr.add_argument("audio")
    tr.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    tr.add_argument("--output-format", choices=["txt", "srt", "vtt", "json"], default=None)
    tr.set_defaults(func=cmd_transcribe)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
