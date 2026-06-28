#!/usr/bin/env bash
# ============================================================
# 9Router 生图模型发现脚本
# 探测 /v1/models/image 端点，返回所有可用生图模型
#
# 用法: bash 9router-list-models.sh
#   或: bash 9router-list-models.sh http://127.0.0.1:20128/v1
# ============================================================

GATEWAY_URL="${1:-http://127.0.0.1:20128/v1}"

echo "=== 9Router 生图可用模型 ==="
echo "网关: $GATEWAY_URL"
echo ""

response=$(curl -s "$GATEWAY_URL/models/image")
echo "$response" | python3 -m json.tool

echo ""
echo "=== 通用模型列表中的 image 标识 ==="
all=$(curl -s "$GATEWAY_URL/models")
echo "$all" | python3 -c "
import json, sys
data = json.load(sys.stdin)
for m in data.get('data', []):
    mid = m['id']
    if mid == 'image':
        print('  image →', m)
    elif 'image' in mid.lower() or 'qwen' in mid.lower():
        print(' ', mid)
"