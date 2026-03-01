#!/bin/bash
# 关闭现有 Chrome（必须，否则调试端口无法挂载）
echo "正在关闭现有 Chrome..."
pkill -a -i "Google Chrome" 2>/dev/null
sleep 2

# 以远程调试模式启动 Chrome
echo "以远程调试模式启动 Chrome..."
/Applications/Google Chrome.app/Contents/MacOS/Google Chrome \
  --remote-debugging-port=9222 \
  --no-first-run \
  2>/dev/null &

sleep 3
echo ""
echo "✓ Chrome 已就绪（调试端口 9222）"
echo "请先在 Chrome 里登录小红书，然后运行："
echo ""
echo "  source venv/bin/activate"
echo "  python reporter.py"
echo ""
