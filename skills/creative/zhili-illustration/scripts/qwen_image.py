#!/usr/bin/env python3
"""
zhili-illustration · qwen-image fallback 生图脚本

mmx image generate 额度耗尽/失败时的备用生图通道。
直连 Aliyun MaaS 工作区（凭证从 9router 本地 DB 读取，不经 9router 转发——
9router v0.5.109 的 images 管线不支持 openai-compatible-* provider，实测 400）。

用法（与 mmx image generate 对齐）：
  python3 qwen_image.py --prompt "..." --aspect-ratio 16:9 \
      --out-dir /tmp/zhili-illustration/ --out-prefix shot-01

输出：{out-dir}/{out-prefix}.png，stdout 最后一行打印路径。
退出码：0 成功；1 失败（stderr 有原因）。
"""
import argparse, base64, json, os, sqlite3, sys, urllib.request, urllib.error

DB = os.path.expanduser("~/.9router/db/data.sqlite")
MODEL = "qwen-image-2.1-pro"   # ⚠️ qwen-image-2.0 在该工作区不存在（实测 400 url error），勿改
SIZES = {
    "16:9": "1664x928",   # 实测可用（2026-10-25）
    "9:16": "928x1664",
    "1:1":  "1024x1024",  # 实测可用
    "4:3":  "1472x1104",
}

def load_creds():
    if not os.path.exists(DB):
        sys.exit(f"ERROR: 9router DB 不存在: {DB}")
    db = sqlite3.connect(f"file:{DB}?mode=ro", uri=True)
    row = db.execute(
        "SELECT json_extract(data,'$.apiKey'),"
        "       json_extract(data,'$.providerSpecificData.baseUrl')"
        " FROM providerConnections"
        " WHERE isActive=1 AND provider LIKE 'openai-compatible-chat-%'"
        "   AND json_extract(data,'$.providerSpecificData.baseUrl') LIKE '%aliyuncs%'"
        " LIMIT 1"
    ).fetchone()
    db.close()
    if not row or not row[0] or not row[1]:
        sys.exit("ERROR: 9router DB 中无活跃 aliyun openai-compatible 连接")
    return row[0], row[1].rstrip("/")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True)
    ap.add_argument("--aspect-ratio", default="16:9")
    ap.add_argument("--out-dir", default="/tmp/zhili-illustration/")
    ap.add_argument("--out-prefix", default="shot-01")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    key, base = load_creds()
    size = SIZES.get(args.aspect_ratio, SIZES["16:9"])
    payload = json.dumps({"model": MODEL, "prompt": args.prompt, "size": size}).encode()
    req = urllib.request.Request(
        f"{base}/images/generations", data=payload,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            resp = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        sys.exit(f"ERROR: HTTP {e.code}: {e.read().decode()[:300]}")
    except Exception as e:
        sys.exit(f"ERROR: 请求失败: {e}")

    data = (resp.get("data") or [{}])[0]
    os.makedirs(args.out_dir, exist_ok=True)
    out = os.path.join(args.out_dir, f"{args.out_prefix}.png")
    if data.get("url"):
        # OSS URL 仅 24h 有效，必须立即下载落盘
        with urllib.request.urlopen(data["url"], timeout=120) as r, open(out, "wb") as f:
            f.write(r.read())
    elif data.get("b64_json"):
        with open(out, "wb") as f:
            f.write(base64.b64decode(data["b64_json"]))
    else:
        sys.exit(f"ERROR: 响应无图片: {json.dumps(resp)[:300]}")

    if not args.quiet:
        print(f"[OK] {MODEL} {size} -> {out} ({os.path.getsize(out)} bytes)", file=sys.stderr)
    print(out)

if __name__ == "__main__":
    main()
