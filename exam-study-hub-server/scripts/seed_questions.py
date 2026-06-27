"""把前端 docs/*.json 的题库灌入数据库（question_topics / questions）。
用法：在 server 目录下 `./.venv/bin/python -m scripts.seed_questions`

题库源文件位于 exam-study-hub-client/docs/，按科目映射。
"""
import json
import re
from pathlib import Path

from app.db.session import SessionLocal
from app.models.catalog import QuestionTopic, Question

DOCS_DIR = Path(__file__).resolve().parent.parent.parent / "exam-study-hub-client" / "docs"

# 科目 → 题库文件
SUBJECT_FILES = {
    "政治": "Politics.json",
    "英语": "English.json",
    "高等数学（一）": "MathOne.json",
    "高等数学（二）": "MathTwo.json",
    "大学语文": "ChineseLiterature.json",
    "教育理论": "EducationTheory.json",
    "民法": "CivilLaw.json",
}

OPTION_PREFIX = re.compile(r"^[A-D][.、．]\s*")


def normalize_option(option: str) -> str:
    return OPTION_PREFIX.sub("", str(option)).strip()


def run():
    db = SessionLocal()
    try:
        topic_added = q_added = 0
        for subject, filename in SUBJECT_FILES.items():
            path = DOCS_DIR / filename
            if not path.exists():
                print(f"跳过 {subject}：未找到 {path}")
                continue
            # 已存在该科目题库则跳过（可重复运行）
            if db.query(QuestionTopic).filter_by(subject=subject).first():
                continue
            bank = json.loads(path.read_text(encoding="utf-8"))
            for t_index, topic in enumerate(bank.get("topics", [])):
                qt = QuestionTopic(subject=subject, name=topic["name"], sort_order=t_index)
                for q_index, q in enumerate(topic.get("questions", [])):
                    qt.questions.append(Question(
                        stem=q["question"],
                        options=[normalize_option(o) for o in q.get("options", [])],
                        answer=str(q.get("answer", "")).strip().upper(),
                        sort_order=q_index,
                    ))
                    q_added += 1
                db.add(qt)
                topic_added += 1
        db.commit()
        print(f"新增知识点 {topic_added} 个、题目 {q_added} 道；"
              f"当前共知识点 {db.query(QuestionTopic).count()}、题目 {db.query(Question).count()}")
    finally:
        db.close()


if __name__ == "__main__":
    run()
