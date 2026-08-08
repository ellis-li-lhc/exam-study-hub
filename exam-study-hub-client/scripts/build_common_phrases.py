#!/usr/bin/env python3
"""从公开的 Tatoeba 英中句对生成英语特训的常用短句库。"""

from __future__ import annotations

import io
import json
import re
import urllib.request
import zipfile
from pathlib import Path


SOURCE_URL = 'https://www.manythings.org/anki/cmn-eng.zip'
OUTPUT_PATH = Path(__file__).resolve().parents[1] / 'docs' / 'EnglishCommonPhrases.json'
GROUP_SIZE = 20
GROUP_COUNT = 24
EXCLUDED_TERMS = {
    'dead', 'die', 'died', 'kill', 'killed', 'fire', 'fight', 'gun', 'weapon',
    'idiot', 'stupid', 'drunk', 'naked', 'sex', 'tom', 'hitler', 'war',
    'kiss', 'shut', 'cuff', 'grab', 'hate', 'love', 'single', 'married',
    'crazy', 'nuts', 'pregnant'
}
EXCLUDED_PHRASES = {'get out', 'go away', 'get away', 'get down', 'get lost', 'back off'}


def is_study_ready(english: str, chinese: str) -> bool:
    words = re.findall(r"[A-Za-z]+(?:'[A-Za-z]+)?", english)
    normalized = english.lower()
    if not 2 <= len(words) <= 7 or not 5 <= len(english) <= 48:
        return False
    if not re.fullmatch(r"[A-Za-z ,.!?'’-]+", english):
        return False
    if any(re.search(rf'\b{re.escape(term)}\b', normalized) for term in EXCLUDED_TERMS):
        return False
    if normalized.strip(" .!?'’") in EXCLUDED_PHRASES:
        return False
    return bool(chinese.strip()) and '汤姆' not in chinese and '湯姆' not in chinese


def normalized_key(text: str) -> str:
    return re.sub(r"[^a-z]", '', text.lower())


def main() -> None:
    request = urllib.request.Request(SOURCE_URL, headers={'User-Agent': 'exam-study-hub-data-import/1.0'})
    with urllib.request.urlopen(request, timeout=45) as response:
        archive = zipfile.ZipFile(io.BytesIO(response.read()))
        rows = archive.read('cmn.txt').decode('utf-8').splitlines()

    selected = []
    seen = set()
    for row in rows:
        parts = row.split('\t')
        if len(parts) < 3:
            continue
        english, chinese, attribution = parts[0].strip(), parts[1].strip(), parts[2].strip()
        key = normalized_key(english)
        if not key or key in seen or not is_study_ready(english, chinese):
            continue
        seen.add(key)
        selected.append({
            'word': english,
            'meaning': chinese,
            'attribution': attribution
        })
        if len(selected) == GROUP_SIZE * GROUP_COUNT:
            break

    if len(selected) != GROUP_SIZE * GROUP_COUNT:
        raise RuntimeError(f'公开语料不足：仅筛到 {len(selected)} 条')

    groups = []
    for index in range(GROUP_COUNT):
        start = index * GROUP_SIZE
        groups.append({
            'id': f'common-{index + 1:02d}',
            'name': f'常用短句 {index + 1:02d}',
            'short': f'短句 {index + 1:02d}',
            'desc': f'公开英中语料精选 · 第 {index + 1} 组',
            'words': selected[start:start + GROUP_SIZE]
        })

    data = {
        'title': '日常短语与短句',
        'intro': f'精选 {len(selected)} 条日常表达，可按组循环听读或一次连续播放。',
        'source': {
            'name': 'Tatoeba English–Mandarin Chinese sentence pairs（ManyThings 整理版）',
            'url': SOURCE_URL,
            'license': 'CC BY 2.0 FR',
            'attribution': 'www.manythings.org/anki and tatoeba.org；每条记录保留原始署名。',
            'accessed': '2026-08-08'
        },
        'groups': groups
    }
    OUTPUT_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f'已生成 {len(selected)} 条短句，共 {len(groups)} 组：{OUTPUT_PATH}')


if __name__ == '__main__':
    main()
