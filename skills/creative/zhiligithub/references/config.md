# 直隶按察使 · 公众号凭证配置参考

# ⚠️ 此文件**不存放**明文凭证 — 明文 APPSECRET 仅存于 `~/.hermes/keys/wx_appsecret.txt`（权限 600，不进 git）
# 此文件仅供**查阅凭证相关字段名 + 维护入口**，运行时通过 cat 命令或 env var 引用。
# 凭证维护：source ~/.hermes/keys/secret-scan-patterns.txt 看真前缀列表，hash 在 scanner 里

APPID: wx38a91c353554588a
APPSECRET: __REDACTED__    # 真值在 ~/.hermes/keys/wx_appsecret.txt；运行时用 $(cat ~/.hermes/keys/wx_appsecret.txt)
CATEGORY_ID: 100

# IP 白名单（服务器出口 IP，需在微信后台配置）
# 当前服务器 IP 段：39.102.x.x
# 建议添加整个 39.0.0.0/8 网段