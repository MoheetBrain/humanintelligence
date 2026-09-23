import zipfile, re, sys, xml.etree.ElementTree as ET
NS={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def sheets(path):
    z=zipfile.ZipFile(path)
    wb=ET.fromstring(z.read('xl/workbook.xml'))
    rels=ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rmap={r.get('Id'):r.get('Target') for r in rels}
    out=[]
    for s in wb.find('m:sheets',NS):
        rid=s.get('{%s}id'%NS['r'])
        tgt=rmap[rid]; tgt=tgt.lstrip('/'); 
        if not tgt.startswith('xl/'): tgt='xl/'+tgt
        out.append((s.get('name'),tgt))
    return z,out
def shared(z):
    try: sst=ET.fromstring(z.read('xl/sharedStrings.xml'))
    except KeyError: return []
    res=[]
    for si in sst.findall('m:si',NS):
        res.append(''.join(t.text or '' for t in si.iter('{%s}t'%NS['m'])))
    return res
def col2n(c):
    n=0
    for ch in c: n=n*26+ord(ch)-64
    return n-1
def rows(z,tgt,ss,maxrows=None):
    data=z.read(tgt)
    for ev,el in ET.iterparse(__import__('io').BytesIO(data)):
        if el.tag=='{%s}row'%NS['m']:
            r={}
            for c in el.findall('m:c',NS):
                ref=c.get('r'); col=col2n(re.match(r'[A-Z]+',ref).group())
                t=c.get('t'); v=c.find('m:v',NS)
                if t=='s' and v is not None: val=ss[int(v.text)]
                elif t=='inlineStr':
                    val=''.join(x.text or '' for x in c.iter('{%s}t'%NS['m']))
                else: val=v.text if v is not None else ''
                r[col]=val
            if r:
                m=max(r)+1; yield [r.get(i,'') for i in range(m)]
            el.clear()
