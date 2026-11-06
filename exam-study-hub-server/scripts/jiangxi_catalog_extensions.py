"""Additional primary university catalogues. Preserve sites, directions and source conflicts."""
from hashlib import sha256
import json
import re
import pdfplumber
from scripts.adult_source_utils import tables

SCHOOLS={'ecjtu':'华东交通大学','ecut':'东华理工大学','jxust':'江西理工大学','jxycu':'宜春学院',
         'jxutcm':'江西中医药大学','juwp':'江西水利电力大学','jxufe':'江西财经大学','jxstnu':'江西科技师范大学',
         'xyc':'新余学院','ncu':'南昌大学'}


def taxonomy(root):
    text=(root.parent/'hubei/exam-categories-2026.txt').read_text()
    text=text.split('四、专科起点升本科招生专业与统一考试科目对照表',1)[1].split('附件 2',1)[0]
    starts=list(re.finditer(r'（([一二三四五六七八])）',text));result={}
    for i,start in enumerate(starts):
        segment=text[start.end():starts[i+1].start()if i+1<len(starts)else len(text)]
        for code,name in re.findall(r'(?m)^(\d{6})\s*\n([^\d\n][^\n]*)',segment):
            result[re.sub(r'\s+','',name)]=(code,str(11+'一二三四五六七八'.index(start[1])))
    return result


def catalogues(root,urls,program,categories):
    rows=[];classified=taxonomy(root)
    policy=urls['policy-2026.html']
    def add(key,major,cat=None,**details):
        source=details.pop('source_file',f'brochure-{key}-2026.html')
        raw_major=major;direction=None
        match=re.fullmatch(r'(.+?)（(.+)）',major)
        if match:major,direction=match.groups()
        national,derived=classified.get(major,(None,None))
        resolved=cat or categories.get(derived)
        # Keep unclassified public names in the archive, without creating a study target.
        row=program('jiangxi',SCHOOLS[key],major,resolved or '理工类',urls[source])
        row.update(major_name_raw=raw_major,major_direction=direction,national_major_code=national,
                   category_source_url=urls[source]if cat else policy,category_name_raw=cat,
                   enrollment_scope='江西省',**details)
        if not resolved:row.update(category_name=None,category_code=None,selection_eligible=False,remarks='来源未公布考试科类，当前尚未核实；不作为备考目标。')
        if row.get('teaching_site') or direction:
            row['major_code']='catalog-'+sha256((raw_major+'|'+(row.get('teaching_site')or'')).encode()).hexdigest()[:16]
        rows.append(row);return row
    for key in ['ecjtu','ecut','jxycu','jxutcm','jxstnu']:
        ts=tables(root/f'brochure-{key}-2026.html')
        if key=='ecjtu':
            table=next(t for t in ts if t and t[0][0]=='培养层次')
            for index,(level,major,cat,form,duration,remark,subjects) in enumerate(table[1:],2):
                if level!='专升本':continue
                row=add(key,major,cat,source_table_row=index,study_form=form,study_duration_raw=duration,
                    exam_subjects_raw=subjects,foreign_language='英语'if '英语'in subjects else None,
                    tuition_amount=1700,tuition_unit='per_academic_year',tuition_raw='1700元/年')
        elif key=='ecut':
            table=next(t for t in ts if t and t[0][-1]=='最低修业年限')
            for index,(num,major,code,discipline,level,form,minimum)in enumerate(table[1:],2):
                if level!='专升本':continue
                row=add(key,major,source_table_row=index,study_form=form,minimum_study_duration_raw=minimum,
                    discipline_raw=discipline,foreign_language='英语',tuition_amount=1700,tuition_unit='per_academic_year',tuition_raw='1700元/年')
                row.update(major_code=code,major_code_raw=code)
        elif key=='jxycu':
            table=next(t for t in ts if t and t[0][0]=='学历层次')
            for index,(level,cat,major,duration,form,special,common)in enumerate(table[1:],2):
                if level!='专升本':continue
                add(key,major,cat,source_table_row=index,study_form=form,study_duration_raw=duration,
                    exam_subjects_raw=common+'、'+special,foreign_language='英语',tuition_amount=1700,
                    tuition_unit='per_academic_year',tuition_raw='1700元/学年')
        elif key=='jxutcm':
            table=next(t for t in ts if t and t[0][:2]==['层次','专业'])
            for index,(level,major,subjects,duration,fee,requirements,method,graduation)in enumerate(table[1:],2):
                if level!='专升本':continue
                cat=next(name for token,name in [('高数（二）','经济管理类'),('大学语文','文史中医类'),('医学综合','医学类')]if token in subjects)
                row=add(key,major,cat,source_table_row=index,study_duration_raw=duration,exam_subjects_raw=subjects,
                    tuition_amount=1700,tuition_unit='per_academic_year',tuition_raw=fee,
                    remarks='报名条件：'+requirements+'；授课形式：'+method+'；毕业条件：'+graduation)
                if major in classified and categories[classified[major][1]]!=cat:
                    row.update(selection_eligible=False,remarks=row['remarks']+'；科目与统考分类不一致，暂不作为备考目标，以省级正式目录为准。')
        else:
            table=next(t for t in ts if t and t[0][-1]=='统考科目')
            for index,(level,major,kind,cat,form,duration,fee,subjects)in enumerate(table[1:],2):
                if level!='专升本':continue
                raw=cat
                row=add(key,major,'医学类'if cat=='医药类'else cat,source_table_row=index,
                    study_form=form,study_duration_raw=duration,tuition_amount=int(fee),
                    tuition_unit='per_academic_year',tuition_raw=fee+'元/年',exam_subjects_raw=subjects)
                row['category_name_raw']=raw
                if major=='药学':row.update(selection_eligible=False,remarks='原文列“医药类、医学综合”，与省级专升本药学科目高数（二）不一致；暂不作为备考目标，待省级正式目录核实。')
    # These two sources explicitly associate each programme with its teaching site.
    for key in ['jxust','juwp']:
        table=next(t for t in tables(root/f'brochure-{key}-2026.html')if t and ((t[0]==['序号','教学点名称','招生专业'])if key=='jxust'else(t[0][:2]==['序号','校外教学点'])))
        for index,r in enumerate(table[1:],2):
            if key=='jxust':seq,site,text=r;address=None
            else:
                seq,site,address,level,text,contact,phone=r
                if not address.startswith(('江西','南昌市','景德镇市','萍乡市','九江市','新余市','鹰潭市','赣州市','吉安市','宜春市','抚州市','上饶市')):continue
            match=re.search(r'专升本(?:\(([^)]+)\))?[:：](.*?)(?=高起|$)',text)
            if not match:continue
            for major in match[2].split('、'):
                details=dict(source_table_row=index,teaching_site=site,teaching_site_address_raw=address)
                if key=='juwp':details.update(study_duration_raw=match[1],tuition_amount=1700,tuition_unit='per_academic_year',tuition_raw='1700元/学年')
                add(key,major,**details)
    with pdfplumber.open(root/'brochure-jxufe-2026.pdf')as pdf:
        for page_index in [1,2]:
            table=next(t for t in pdf.pages[page_index].extract_tables()if len(t[0])in(5,6))
            for index,r in enumerate(table[1:]if page_index==1 else table,2 if page_index==1 else 1):
                if r[0]=='高起本':break
                major=re.sub(r'\s+','',r[1]);duration,form,cat=r[2:5]
                add('jxufe',major,cat,source_file='brochure-jxufe-2026.pdf',source_page=page_index+1,source_table_row=index,
                    study_duration_raw=duration,study_form=form,foreign_language='英语',tuition_amount=1700,
                    tuition_unit='per_academic_year',tuition_raw='1700元/学年')
    # Review files preserve visually checked numeric glyphs and image transcriptions.
    for key in ['xyc','ncu']:
        review=json.loads((root/f'brochure-{key}-2026-reviewed.json').read_text())
        for source,digest in review['source_hashes'].items():
            if sha256((root/source).read_bytes()).hexdigest()!=digest:raise ValueError('附件已变化，须重新目视核对：'+source)
        if key=='xyc':
            for index,r in enumerate(review['rows'],1):
                cat,major,duration=r
                add(key,major,cat,source_file='brochure-xyc-2026-2.jpg',source_table_row=index,
                    study_duration_raw=duration,foreign_language='英语',tuition_amount=2100 if cat=='艺术类'else 1700,
                    tuition_unit='per_academic_year',tuition_raw='2100元/年'if cat=='艺术类'else '1700元/年')
        else:
            with pdfplumber.open(root/'brochure-ncu-2026.pdf')as pdf:
                table=pdf.pages[0].extract_tables()[1]
                selected=[r for r in table if len(r)==11 and r[1]=='专升本' and r[6]=='√']
                for index,r in enumerate(selected,9):
                    cat={'经管':'经济管理类','医学':'医学类','法学':'法学类','文史':'文史中医类','理工':'理工类'}[r[5]]
                    add(key,r[2],cat,source_file='brochure-ncu-2026.pdf',source_page=1,source_table_row=index,
                        study_form=r[3],study_duration_raw=review['study_duration_raw'],tuition_amount=review['tuition_amount'],
                        tuition_unit='per_academic_year',tuition_raw='1700元/学年',remarks='；'.join(filter(None,[r[10], '医学门类须符合相应专业学历、执业资格及在职对口条件；护理学须护士执业证书，详见简章第2页。' if cat=='医学类' or r[2]=='药学' else None])),teaching_site='校本部' if '限本部'in (r[10]or'')else None)
                if not any('网络空间安全'in (r[0]or'')for r in table):raise ValueError('南昌大学末行结构变化')
                add(key,'网络空间安全','理工类',source_file='brochure-ncu-2026.pdf',source_page=1,source_table_row=32,
                    study_form='非脱产',study_duration_raw=review['study_duration_raw'],tuition_amount=review['tuition_amount'],
                    tuition_unit='per_academic_year',tuition_raw='1700元/学年',remarks='江西省内限本部招生',teaching_site='校本部')
    expected={'华东交通大学':14,'东华理工大学':20,'江西理工大学':26,'宜春学院':22,'江西中医药大学':8,'江西水利电力大学':47,'江西财经大学':10,'江西科技师范大学':16,'新余学院':25,'南昌大学':24}
    from collections import Counter
    if Counter(r['institution_name']for r in rows)!=expected:raise ValueError('扩展目录的来源计数变化，请逐校复核')
    return rows,[dict(institution_name=name,source_urls=[urls[f'brochure-{key}-2026.html']])for key,name in SCHOOLS.items()]
