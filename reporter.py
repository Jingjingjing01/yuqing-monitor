"""自动举报脚本 - 连接已运行的 Chrome，自动完成小红书举报流程"""

import asyncio
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from playwright.async_api import async_playwright
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
CDP_URL = "http://localhost:9222"   # Chrome 远程调试地址


# ── 数据库操作 ────────────────────────────────────────────

def get_pending_notes():
    """获取待举报笔记（高/中风险，状态=待投诉，有链接）"""
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, sslmode="require")
    cur = conn.cursor()
    cur.execute("""
        SELECT n.file_id, n.idx, n.title, n.note_url,
               n.risk_level, n.report_category, n.report_text
        FROM notes n
        WHERE n.report_status = '待投诉'
          AND n.risk_level IN ('高风险', '中风险')
          AND n.note_url IS NOT NULL AND n.note_url != ''
        ORDER BY
          CASE n.risk_level WHEN '高风险' THEN 0 ELSE 1 END,
          n.influence_score DESC
    """)
    notes = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return notes


def mark_reported(file_id, idx):
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor, sslmode="require")
    cur = conn.cursor()
    cur.execute("UPDATE notes SET report_status='已投诉' WHERE file_id=%s AND idx=%s",
                (file_id, idx))
    conn.commit()
    cur.close()
    conn.close()


# ── 举报核心逻辑 ──────────────────────────────────────────

async def click_report_button(page):
    """找到并点击举报按钮（兼容多种页面结构）"""
    # 策略1：直接找文字为"举报"的按钮
    try:
        btn = page.get_by_text("举报", exact=True).first
        await btn.wait_for(timeout=4000)
        await btn.click()
        return
    except Exception:
        pass

    # 策略2：先点"..."更多菜单，再点举报
    try:
        more = page.locator("[class*='more'], [class*='extra'], [class*='option']").first
        await more.click(timeout=3000)
        await page.wait_for_timeout(600)
        await page.get_by_text("举报", exact=True).first.click()
        return
    except Exception:
        pass

    raise RuntimeError("找不到举报按钮，请检查页面是否已完全加载，或笔记是否已被删除")


async def select_category(page, category):
    """在举报弹窗中选择罪名"""
    # 等待举报弹窗出现
    await page.wait_for_selector("text=举报笔记", timeout=8000)
    await page.wait_for_timeout(500)

    # 滚动到罪名并点击
    item = page.get_by_text(category, exact=True).first
    await item.scroll_into_view_if_needed()
    await item.click()
    await page.wait_for_timeout(400)


async def submit_report(page, report_text, category):
    """点击下一步，处理复杂/简单两种流程后提交"""
    await page.get_by_role("button", name="下一步").click()
    await page.wait_for_timeout(1500)

    # 检测是否有文字输入框（复杂流程）
    textarea = page.locator("textarea").first
    has_textarea = await textarea.is_visible().catch(lambda _: False) \
        if hasattr(textarea, 'catch') else False
    try:
        has_textarea = await textarea.is_visible()
    except Exception:
        has_textarea = False

    if has_textarea:
        print(f"  → 复杂流程：填写举报描述")
        desc = (report_text or f"该笔记存在{category}行为，损害摩天轮票务品牌权益。")[:200]
        await textarea.fill(desc)
        await page.wait_for_timeout(400)
    else:
        print(f"  → 简单流程：直接提交")

    await page.get_by_role("button", name="提交").click()
    await page.wait_for_timeout(2000)


async def report_one(context, note):
    """完整举报单条笔记"""
    page = await context.new_page()
    try:
        print(f"\n  → 打开笔记：{note['title'][:50]}")
        await page.goto(note["note_url"], wait_until="domcontentloaded", timeout=30000)
        await page.wait_for_timeout(2000)

        print(f"  → 点击举报按钮")
        await click_report_button(page)
        await page.wait_for_timeout(1000)

        print(f"  → 选择罪名：{note['report_category']}")
        await select_category(page, note["report_category"])

        print(f"  → 提交举报")
        await submit_report(page, note.get("report_text", ""), note["report_category"])

        print(f"  ✓ 举报提交完成")
        input("  查看页面确认无误后，按 Enter 关闭此标签页...")
        await page.close()
        return True

    except Exception as e:
        print(f"  ✗ 出错：{e}")
        input("  按 Enter 关闭此标签页（该条将跳过）...")
        await page.close()
        return False


# ── 主流程 ────────────────────────────────────────────────

async def main():
    notes = get_pending_notes()
    if not notes:
        print("✓ 没有待举报笔记（高/中风险且状态为「待投诉」且有链接）")
        return

    print(f"共找到 {len(notes)} 条待举报笔记（高风险优先）\n")

    async with async_playwright() as p:
        try:
            browser = await p.chromium.connect_over_cdp(CDP_URL)
        except Exception:
            print("✗ 无法连接 Chrome，请先运行：bash start_chrome.sh")
            return

        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        print("✓ 已连接 Chrome\n")

        for i, note in enumerate(notes):
            print(f"[{i+1}/{len(notes)}] {note['risk_level']}  ·  {note['title'][:50]}")
            print(f"  罪名：{note['report_category']}")
            print(f"  链接：{note['note_url']}")

            action = input("  按 Enter 开始举报 / 输入 s 跳过 / 输入 q 退出：").strip().lower()
            if action == "q":
                print("\n退出举报流程")
                break
            if action == "s":
                print("  跳过")
                continue

            success = await report_one(context, note)
            if success:
                mark_reported(note["file_id"], note["idx"])
                print(f"  ✓ 数据库状态已更新为「已投诉」")

    print("\n举报流程结束")


if __name__ == "__main__":
    asyncio.run(main())
