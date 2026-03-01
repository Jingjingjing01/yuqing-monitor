"""
监听 ~/Desktop/摩天轮舆情管理/ 文件夹
新 Excel 文件出现 → 自动上传 → 自动触发分析
"""

import time
import requests
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

WATCH_DIR = Path.home() / "Desktop" / "摩天轮舆情管理"
SERVER = "http://localhost:5001"


class ExcelHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        path = Path(event.src_path)
        if path.suffix not in (".xlsx", ".xls"):
            return
        # 等文件写完
        time.sleep(1)
        print(f"\n[检测到新文件] {path.name}")
        self._upload_and_analyze(path)

    def _upload_and_analyze(self, path: Path):
        # 1. 上传
        try:
            with open(path, "rb") as f:
                resp = requests.post(
                    f"{SERVER}/upload",
                    files={"file": (path.name, f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
                    timeout=30,
                )
            data = resp.json()
        except Exception as e:
            print(f"  [上传失败] {e}")
            return

        if "error" in data:
            print(f"  [上传错误] {data['error']}")
            return

        file_id = data["file_id"]
        total = data["total"]
        print(f"  [上传成功] {total} 条笔记，file_id={file_id}")

        # 2. 触发分析（SSE 流式读取进度）
        print(f"  [开始分析] ...")
        try:
            with requests.get(f"{SERVER}/analyze/{file_id}", stream=True, timeout=300) as r:
                for line in r.iter_lines():
                    if not line:
                        continue
                    text = line.decode("utf-8")
                    if text.startswith("data:"):
                        import json
                        payload = json.loads(text[5:].strip())
                        if payload.get("done"):
                            print(f"  [分析完成] 请打开 http://localhost:5001 查看结果")
                        else:
                            cur = payload.get("current", 0)
                            tot = payload.get("total", total)
                            risk = payload.get("risk_level", "")
                            title = payload.get("title", "")
                            print(f"  [{cur}/{tot}] {risk} — {title[:30]}")
        except Exception as e:
            print(f"  [分析出错] {e}")


if __name__ == "__main__":
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    print(f"监听文件夹: {WATCH_DIR}")
    print(f"服务地址:   {SERVER}")
    print("等待新 Excel 文件...\n")

    handler = ExcelHandler()
    observer = Observer()
    observer.schedule(handler, str(WATCH_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
