"""Lossless text cells and explicit rowspan expansion for official HTML tables."""
from html.parser import HTMLParser
import re
from scripts.scrape_hubei import expand

class TableReader(HTMLParser):
    def __init__(self):
        super().__init__(); self.tables=[]; self.stack=[]
    def handle_starttag(self, tag, attrs):
        if tag=='table': self.stack.append({'rows':[], 'row':None, 'cell':None})
        if not self.stack: return
        frame=self.stack[-1]
        if tag=='tr': frame['row']=[]
        if tag in ('td','th') and frame['row'] is not None: frame['cell']=[dict(attrs),[]]
    def handle_data(self, data):
        if self.stack and self.stack[-1]['cell'] is not None: self.stack[-1]['cell'][1].append(data)
    def handle_endtag(self, tag):
        if not self.stack:return
        frame=self.stack[-1]
        if tag in ('td','th') and frame['cell'] is not None:
            attrs, parts=frame['cell'];frame['row'].append((attrs,re.sub(r'\s+','',''.join(parts))));frame['cell']=None
        if tag=='tr' and frame['row'] is not None: frame['rows'].append(frame['row']);frame['row']=None
        if tag=='table': self.tables.append(self.stack.pop()['rows'])

def tables(path):
    reader=TableReader();reader.feed(path.read_text(encoding='utf-8'))
    return [list(expand(table)) for table in reader.tables]
