#!/bin/bash
echo "正在关闭现有 Chrome..."
pkill -x "Google Chrome" 2>/dev/null || true
sleep 4

echo "以远程调试模式启动 Chrome..."
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --remote-debugging-port=9222 \
  --no-first-run > /dev/null 2>&1 &

# 等待调试端口就绪（最多 15 秒）
echo "等待 Chrome 启动..."
for i in {1..15}; do
  sleep 1
  if curl -s http://localhost:9222/json > /dev/null 2>&1; then
    echo ""
    echo "✓ Chrome 已就绪，调试端口 9222 开放"
    echo ""
    echo "请在弹出的 Chrome 窗口里登录小红书，然后运行："
    echo "  python reporter.py"
    echo ""
    exit 0
  fi
  printf "."
done

echo ""
echo "✗ 端口 9222 未响应，请重试"
