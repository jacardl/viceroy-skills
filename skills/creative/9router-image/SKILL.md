---
name: 9router-image
description: Image generation via 9Router local gateway (cx/gpt-5.5-image etc.). Use when generating images for articles, reports, or social media, and 9Router is the available image backend.
permissions:
  - http://127.0.0.1:20128/  # local 9Router gateway only; no external hosts, no remote script fetching
---

# 9Router Image Generation

通过本地 9Router 网关生成图像（text-to-image），复用 Hermes `image_generate` 工具，零额外 SDK 依赖。

## 快速验证（确认可用）

```bash
# 探测生图可用模型
curl -s http://127.0.0.1:20128/v1/models/image | python3 -m json.tool

# 预期：返回 cx/gpt-5.5-image / cx/gpt-5.4-image / cx/gpt-5.3-image

# curl 直测（需先填入 KEY）
KEY="sk-your-9router-key"
curl -s -X POST http://127.0.0.1:20128/v1/images/generations \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $KEY" \
  -d '{"model":"cx/gpt-5.5-image","prompt":"a red rose","n":1,"size":"1024x1024"}' \
  --max-time 120 | python3 -m json.tool
```

## 完整架构

```
image_generate 工具（Hermes 统一入口）
  → image_gen_registry.get_active_provider()
    → config.yaml image_gen.provider = "9router"  ← 必须
    → NineRouterImageGenProvider.generate()
      → POST http://127.0.0.1:20128/v1/images/generations
        → 9Router 识别 model 前缀 "cx/" → 路由到内置 cx provider
        → cx/gpt-5.5-image API（真正生图）
        → 返回 base64 PNG
      → 保存到 $HERMES_HOME/cache/images/9router_image_*.png
```

## 配置（缺一不可）

**文件：** `~/.hermes/config.yaml`

```yaml
providers:
  9router:
    api: http://127.0.0.1:20128/v1
    api_key: sk-你的9router-gateway-key   # 9Router 网关自身的 key，不是 cx 的 key

image_gen:
  provider: 9router     # ← 必须写死
  model: cx/gpt-5.5-image   # 可选，默认 cx/gpt-5.5-image
```

⚠️ `api_key` 是 **9Router 网关** 的 key（注册 9Router 时拿到的），**不是 cx 或 qwen 的 key**。9Router 在内部路由到 cx provider，cx 的认证在 9Router 服务端配置。

## 插件源码

完整源码在 `references/9router-plugin/`（含 `__init__.py` + `plugin.yaml`）。也可直接参考该目录复制到其他 Hermes 安装。

## 可用模型

| model id | 说明 | 推理时间 |
|---|---|---|
| `cx/gpt-5.5-image` | 推荐默认 | ~99s/张 |
| `cx/gpt-5.4-image` | 次新 | ~90s/张 |
| `cx/gpt-5.3-image` | 较旧 | ~80s/张 |

⚠️ **`image` 是 chat 模型**（归属 combo，在 `/v1/models` 里），**不是生图模型**，不能用于 `/v1/images/generations`。实测报错：`Provider does not support image generation`。

## 常见错误排查

| 错误信息 | 原因 | 解决 |
|---|---|---|
| `No credentials for provider: openai` | model `image` 无前缀，9Router 按 OpenAI 路由 | 改用 `cx/gpt-5.5-image` |
| `No credentials for provider: qwen` | model 带 `qwen/` 前缀，但 9Router 未配 qwen key | 改用 `cx/gpt-5.5-image` |
| `Provider does not support image generation` | model 是 chat 模型（如 `image`、`qwen-image-2.0`） | 改用 `cx/gpt-5.5-image` |
| 401 Unauthorized | 9Router key 错误或过期 | 检查 `providers.9router.api_key` |
| Connection refused | 9Router 网关未启动 | 启动 9Router：`9router serve` 或对应命令 |

## 生成图像（标准流程）

1. 确保 `config.yaml` 中 `image_gen.provider: 9router`
2. 直接调用 `image_generate` 工具，prompt 即可
3. 图像保存在 `~/.hermes/cache/images/9router_image_*.png`，也可指定输出路径

## Prompt 优化建议

- portrait（1024×1792）比 landscape（1792×1024）更大，prompt **宜精简**避免 120s 超时
- 简短、明确的英文描述效果最佳
- 示例（portrait）：`A worried small furniture store owner staring at a glowing AI recommendation screen`
- 示例（landscape）：`Split-screen: left shows traditional SEO ranking battlefield, right shows AI overview answer box with brand highlighted`
