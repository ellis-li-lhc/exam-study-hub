"""把从知乎复制来的政治知识点 HTML 清洗成结构化 JSON（知识点速记 + 简答题）。
第三方整理内容，仅供个人备考；不声称官方真题。

用法：在 server 目录下
  ./.venv/bin/python -m scripts.clean_politics_html <输入html.json> [输出.json]
不传输出路径时默认写到 /tmp/Politics_knowledge.json 供预览。
"""
import html
import json
import re
import sys
from pathlib import Path

P_BLOCK = re.compile(r"<p\b[^>]*>(.*?)</p>", re.S)
SVG = re.compile(r"<svg\b.*?</svg>", re.S)
TAG = re.compile(r"<[^>]+>")
BOLD = re.compile(r"<b\b[^>]*>(.*?)</b>", re.S)


def clean(fragment: str) -> str:
    s = SVG.sub("", fragment)        # 去掉内嵌图标
    s = TAG.sub("", s)               # 去掉所有标签
    s = html.unescape(s)             # 解码 &quot; &amp; 等
    s = s.replace("\u3000", " ").replace("\xa0", " ")  # 全角空格/不间断空格
    return re.sub(r"\s+", " ", s).strip()


def bold_text(fragment: str) -> str:
    return clean(" ".join(BOLD.findall(fragment)))


def parse(raw: str) -> dict:
    blocks = [(clean(b), bold_text(b)) for b in P_BLOCK.findall(raw)]

    memory, essay = [], []
    section = None
    cur_essay = None
    for text, bold in blocks:
        if not text:
            continue
        if "选择题题库" in text:
            section = "memory"
            continue
        if "简述题库" in text or "简答题库" in text:
            if cur_essay:
                essay.append(cur_essay)
                cur_essay = None
            section = "essay"
            continue

        if section == "memory":
            m = re.match(r"^(\d+)[.、]\s*(.*)$", text)
            if not m:
                continue
            body = m.group(2).strip()
            # 题干：答案（按第一个冒号切）
            parts = re.split(r"[:：]", body, maxsplit=1)
            if len(parts) == 2 and parts[1].strip():
                q, a = parts[0].strip(), parts[1].strip().rstrip("。.").strip()
            else:
                q, a = body.rstrip("。.").strip(), bold
            memory.append({"q": q, "a": a})

        elif section == "essay":
            # 整段加粗且以「N、」开头 → 新的简答题
            head = re.match(r"^(\d+)[、.]\s*(.*)$", text)
            if head and bold and head.group(0).startswith(head.group(1)):
                if cur_essay:
                    essay.append(cur_essay)
                cur_essay = {"q": head.group(2).strip(), "a": []}
            elif cur_essay is not None:
                line = re.sub(r"^答[:：]\s*", "", text).strip()
                if line:
                    cur_essay["a"].append(line)
    if cur_essay:
        essay.append(cur_essay)

    for e in essay:
        e["a"] = "\n".join(e["a"])
    return {
        "title": "2025 年成人高考专升本《政治》知识点速记",
        "source": "知乎专栏（华泰教育集团整理）",
        "sourceUrl": "https://zhuanlan.zhihu.com/p/1946939619007521869",
        "note": "第三方整理，仅供个人备考；以官方教材与考试大纲为准。",
        "memory": memory,
        "essay": essay,
    }


def run():
    args = [a for a in sys.argv[1:]]
    if not args:
        print("用法: python -m scripts.clean_politics_html <输入html.json> [输出.json]")
        return
    raw = Path(args[0]).read_text(encoding="utf-8")
    data = parse(raw)
    out = Path(args[1]) if len(args) > 1 else Path("/tmp/Politics_knowledge.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"知识点速记: {len(data['memory'])} 条")
    print(f"简答题: {len(data['essay'])} 条")
    print("\n速记样例:")
    for item in data["memory"][:4]:
        print(f"  Q: {item['q']}\n  A: {item['a']}")
    print("\n简答样例:")
    if data["essay"]:
        e = data["essay"][0]
        print(f"  Q: {e['q']}\n  A: {e['a'][:120]}...")
    print(f"\n已写入 {out}")


if __name__ == "__main__":
    run()
