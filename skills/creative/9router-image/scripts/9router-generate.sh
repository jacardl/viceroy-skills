#!/usr/bin/env bash
# ============================================================
# 9Router 图像生成直调脚本（无需 Hermes / image_generate 工具）
#
# 用法:
#   bash 9router-generate.sh "a red rose" 1024x1024
#   bash 9router-generate.sh "sunset" 1792x1024 landscape
#   bash 9router-generate.sh "portrait" 1024x1792 portrait
#
# 参数:
#   $1 prompt       (必需) 英文 prompt
#   $2 size         (可选) 1024x1024 | 1792x1024 | 1024x1792，默认 1024x1024
#   $3 aspect_label (可选) landscape | square | portrait，影响显示说明
# ============================================================

set -euo pipefail

GATEWAY_URL="${GATEWAY_URL:-http://127.0.0.1:20128/v1}"
MODEL="${MODEL:-cx/gpt-5.5-image}"
TIMEOUT="${TIMEOUT:-120}"

PROMPT="${1:-}"
SIZE="${2:-1024x1024}"
LABEL="${3:-square}"

if [[ -z "$PROMPT" ]]; then
  echo "用法: $0 <prompt> [size] [label]"
  echo "示例: $0 \"a red rose\" 1024x1024 square"
  exit 1
fi

# 从 config.yaml 读取 key（需 python3 + pyyaml）
CONFIG_KEY=""
if command -v python3 &>/dev/null; then
  CONFIG_KEY=$(python3 -c "
import yaml, os
try:
    cfg = yaml.safe_load(open(os.path.expanduser('~/.hermes/config.yaml')))
    key = cfg.get('providers', {}).get('9router', {}).get('api_key', '')
    print(key)
except:
    print('')
" 2>/dev/null || true)
fi

if [[ -z "$CONFIG_KEY" ]]; then
  echo "错误: 请设置 GATEWAY_URL 和 API_KEY，或确保 ~/.hermes/config.yaml 中配置了 providers.9router.api_key"
  echo ""
  echo "示例:"
  echo "  GATEWAY_URL=http://127.0.0.1:20128/v1 \\"
  echo "  API_KEY=sk-your-key \\"
  echo "  bash $0 \"a red rose\""
  exit 1
fi

echo "生成图像..."
echo "  模型: $MODEL"
echo "  Prompt: $PROMPT"
echo "  尺寸: $SIZE ($LABEL)"
echo ""

response=$(curl -s --max-time "$TIMEOUT" \
  -X POST "$GATEWAY_URL/images/generations" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $CONFIG_KEY" \
  -d "$(jq -n \
    --arg model "$MODEL" \
    --arg prompt "$PROMPT" \
    --arg size "$SIZE" \
    '{model: $model, prompt: $prompt, n: 1, size: $size}')")

# 检查错误
if echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if 'error' not in d else 1)" 2>/dev/null; then
  b64=$(echo "$response" | python3 -c "import json,sys; d=json.load(sys.stdin); print(d['data'][0]['b64_json'])")
  filename="9router_$(date +%Y%m%d_%H%M%S).png"
  echo "$b64" | python3 -m base64 -d > "$filename"
  echo "✅ 已保存: $filename"
else
  echo "❌ 失败:"
  echo "$response" | python3 -m json.tool
  exit 1
fi
