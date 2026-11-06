"""Correct two legacy master-data entries; leave user records and other majors intact."""
import json
from app.db.session import SessionLocal
from app.models.catalog import Major, MajorSubject
from scripts.seed import MAJORS

CODES={'yingyong-xinli','xinxi-guanli'}


def repair(db):
    changed=[]
    for expected in MAJORS:
        if expected['code']not in CODES:continue
        major=db.query(Major).filter_by(code=expected['code']).one()
        before=dict(category=major.category,subjects=[s.subject for s in major.subjects])
        major.category=expected['category']
        if before['subjects']!=expected['subjects']:major.subjects=[MajorSubject(subject=s)for s in expected['subjects']]
        after=dict(category=major.category,subjects=[s.subject for s in major.subjects])
        if before!=after:changed.append(dict(code=major.code,name=major.name,before=before,after=after))
    db.flush();return changed


def run():
    with SessionLocal.begin()as db:changes=repair(db)
    print(json.dumps(changes,ensure_ascii=False))

if __name__=='__main__':run()
