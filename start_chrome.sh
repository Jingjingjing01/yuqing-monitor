#!/bin/bash
echo "正在关闭现有 Chrome..."
pkill -a -i "Google Chrome" 2>/dev/null
sleep 2

echo "以远程调试模式启动 Chrome..."
open -a "Google Chrome" --args --remote-debugging-port=9222 --no-first-run

sleep 2
echo ""
echo "✓ Chrome 已启动（调试端口 9222）"
echo "请先在 Chrome 里登录小红书，然后运行："
echo ""
echo "  source venv/bin/activate"
echo "  python reporter.py"
echo ""
