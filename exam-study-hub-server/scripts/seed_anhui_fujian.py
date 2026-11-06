"""Transactional and repeatable Anhui/Fujian import; no changes to other provinces."""
import json
from app.db.session import SessionLocal
from scripts.adult_catalog_import import DATA, import_catalog


def import_anhui_fujian(db,data_dir=DATA):
    counts={}
    for code in ['anhui','fujian']:
        manifest=json.loads((data_dir/f'{code}-manifest.json').read_text())
        counts[code]=import_catalog(db,code,manifest['province_name'],manifest['coverage_note'],data_dir)
    return counts


def run():
    with SessionLocal.begin()as db:counts=import_anhui_fujian(db)
    print(json.dumps(counts,ensure_ascii=False))

if __name__=='__main__':run()
