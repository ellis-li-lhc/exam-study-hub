"""Scoped, transactional and repeatable imports for Hunan and Jiangxi."""
import json
from pathlib import Path
from app.db.session import SessionLocal

DATA=Path(__file__).resolve().parent.parent/'scraped-data'
COVERAGE={
    'hunan':('湖南','已接入2026省级目录56所院校677条专升本专业、2024—2025省控线16条、2025两轮科类征集238条；另5校仅历史征集，暂无院校实际录取线'),
    'jiangxi':('江西','已接入14所院校2026官方资料297条专业/教学点记录（255个院校专业组合）、2025普通统考省控线8条；非全省完整目录，暂无院校实际录取线，不含一村一名大学生专项；3条科类待核实或科目冲突记录不作为备考目标'),
}
from scripts.adult_catalog_import import import_catalog


def import_province(db,province_code,data_dir=DATA):
    name,note=COVERAGE[province_code]
    return import_catalog(db,province_code,name,note,data_dir)


def import_hunan_jiangxi(db):
    return {province:import_province(db,province)for province in COVERAGE}


def run():
    with SessionLocal.begin() as db:counts=import_hunan_jiangxi(db)
    print(json.dumps(counts,ensure_ascii=False))

if __name__=='__main__':run()
