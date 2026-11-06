"""Transactional and repeatable Sichuan/Chongqing import; no changes to other provinces."""
import json
from app.db.session import SessionLocal
from scripts.adult_catalog_import import DATA, import_catalog


def import_sichuan_chongqing(db,data_dir=DATA):
    counts={}
    for code in ['sichuan','chongqing']:
        manifest=json.loads((data_dir/f'{code}-manifest.json').read_text())
        counts[code]=import_catalog(db,code,manifest['province_name'],manifest['coverage_note'],data_dir)
    from scripts.sichuan_current_catalog import import_current
    counts['sichuan']['plans_added'] += import_current(db,data_dir)
    return counts


def run():
    with SessionLocal.begin()as db:counts=import_sichuan_chongqing(db)
    print(json.dumps(counts,ensure_ascii=False))

if __name__=='__main__':run()
