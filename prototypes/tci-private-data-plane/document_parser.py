"""Bounded synthetic-format parsers, not production malware screening."""
from __future__ import annotations
import io,zipfile,xml.etree.ElementTree as ET,math,base64,json,subprocess,sys
from datetime import date,datetime,time
from pathlib import Path
from pypdf import PdfReader
from openpyxl import load_workbook

MAX_FILE=256*1024
MAX_EXPANDED=8*1024*1024
MAX_SEGMENTS=3000
MAX_TEXT=256*1024
FORMATS={".txt",".pdf",".docx",".xlsx"}
W="{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
METHOD="0.2.0-alpha.2"
class UnsupportedDocument(ValueError):pass

def _check_text(s):
    if any(ord(c)<32 and c not in "\n\r\t" for c in s):raise UnsupportedDocument("Unsupported control content")
    return s
def _xml(data):
    if b"<!DOCTYPE" in data.upper() or b"<!ENTITY" in data.upper():raise UnsupportedDocument("Unsupported XML declaration")
    return ET.fromstring(data)
def _ooxml(raw,required):
    try:z=zipfile.ZipFile(io.BytesIO(raw))
    except (zipfile.BadZipFile,OSError) as e:raise UnsupportedDocument("Invalid Office package") from e
    try:
        infos=z.infolist()
        if len(infos)>250 or sum(i.file_size for i in infos)>MAX_EXPANDED:raise UnsupportedDocument("Office package size limit")
        names=[i.filename for i in infos]
        if len(set(names))!=len(names) or required not in names or "[Content_Types].xml" not in names:raise UnsupportedDocument("Invalid Office document structure")
        for i in infos:
            n=i.filename.lower()
            if i.flag_bits&1 or n.startswith("/") or "\\" in n or ".." in n.split("/") or any(x in n for x in ["vbaproject","activex","embeddings/","externallinks/","oleobject"]):raise UnsupportedDocument("Unsupported Office package feature")
            if n.endswith(".rels"):
                for r in _xml(z.read(i)):
                    if r.attrib.get("TargetMode","").lower()=="external":raise UnsupportedDocument("External Office relationships unsupported")
            elif n.endswith(".xml"):_xml(z.read(i))
        return z
    except Exception:z.close();raise
def _segments_add(out,text,location,pair=None):
    if text:
        _check_text(text)
        if len(out)>=MAX_SEGMENTS:raise UnsupportedDocument("Document segment limit")
        out.append({"text":text,"location":location,**({"pair":pair} if pair else {})})
def _docx(raw):
    out=[]
    with _ooxml(raw,"word/document.xml") as z:
        root=_xml(z.read("word/document.xml"));body=root.find(W+"body")
        if body is None:raise UnsupportedDocument("Missing document body")
        if root.findall(".//"+W+"altChunk") or root.findall(".//"+W+"instrText") or root.findall(".//"+W+"drawing"):raise UnsupportedDocument("Unsupported Word content")
        paragraph=0;table=0
        def text(node):return "".join(t.text or "" for t in node.iter(W+"t"))
        for child in body:
            if child.tag==W+"p":
                paragraph+=1;_segments_add(out,text(child),f"Body paragraph {paragraph}")
            elif child.tag==W+"tbl":
                table+=1
                for rownum,row in enumerate(child.findall(W+"tr"),1):
                    cells=row.findall(W+"tc")
                    if any(c.findall(".//"+W+"tbl") or c.findall(".//"+W+"gridSpan") or c.findall(".//"+W+"vMerge") for c in cells):raise UnsupportedDocument("Nested or merged Word table unsupported")
                    values=[text(c) for c in cells]
                    if len(values)==2 and all(values):
                        _segments_add(out,values[0]+": "+values[1],f"Table {table}, row {rownum}, cells 1–2",{"label":values[0],"value":values[1],"labelLocation":f"Table {table}, row {rownum}, cell 1","valueLocation":f"Table {table}, row {rownum}, cell 2"})
                    else:
                        for cnum,val in enumerate(values,1):_segments_add(out,val,f"Table {table}, row {rownum}, cell {cnum}")
    return out
def _xlsx(raw):
    with _ooxml(raw,"xl/workbook.xml"):pass
    out=[];wb=load_workbook(io.BytesIO(raw),read_only=True,data_only=False,keep_links=False)
    try:
        if len(wb.worksheets)>20:raise UnsupportedDocument("Worksheet limit")
        for ws in wb.worksheets:
            if ws.sheet_state!="visible":continue
            if (ws.max_row or 0)>1000 or (ws.max_column or 0)>30:raise UnsupportedDocument("Worksheet dimension limit")
            for row in ws.iter_rows(max_col=2,max_row=ws.max_row or 0):
                if len(row)<2:continue
                a,b=row
                if a.data_type=="f" or b.data_type=="f" or not isinstance(a.value,str) or not a.value.strip():continue
                # Literal cell values only. Preserve type and number format; no formula evaluation or display inference.
                val=b.value
                if isinstance(val,str):display=val;kind="text";raw_value=val
                elif isinstance(val,bool):display=str(val);kind="boolean";raw_value=val
                elif isinstance(val,(int,float)) and math.isfinite(val):display=str(val);kind="number";raw_value=val
                elif isinstance(val,(date,datetime,time)):display=val.isoformat();kind="date/time";raw_value=display
                else:continue
                if not display.strip():continue
                al=f"Sheet {ws.title}!{a.coordinate}";bl=f"Sheet {ws.title}!{b.coordinate}"
                _segments_add(out,a.value+": "+display,f"{al}–{b.coordinate}",{"label":a.value,"value":display,"labelLocation":al,"valueLocation":bl,"valueType":kind,"rawValue":raw_value,"numberFormat":b.number_format})
    finally:wb.close()
    return out
def _pdf(raw):
    if not raw.startswith(b"%PDF-"):raise UnsupportedDocument("Invalid PDF header")
    reader=PdfReader(io.BytesIO(raw),strict=True)
    if reader.is_encrypted:raise UnsupportedDocument("Encrypted PDF unsupported")
    root=reader.trailer["/Root"]
    if any(k in root for k in ["/OpenAction","/AA","/AcroForm","/Names"]):raise UnsupportedDocument("Interactive or embedded PDF content unsupported")
    if len(reader.pages)>20:raise UnsupportedDocument("PDF page limit")
    out=[]
    for num,page in enumerate(reader.pages,1):
        if any(k in page for k in ["/Annots","/AA"]):raise UnsupportedDocument("Interactive PDF page unsupported")
        # Synthetic text-layer documents only; no OCR or image processing.
        contents=page.get_contents()
        if contents is not None and len(contents.get_data())>MAX_EXPANDED:raise UnsupportedDocument("PDF page content limit")
        text=page.extract_text() or ""
        for line,s in enumerate(text.splitlines(),1):_segments_add(out,s,f"PDF page {num}, extracted line {line}")
    if not out:raise UnsupportedDocument("No supported PDF text layer")
    return out
def _parse_document(filename,raw):
    suffix=Path(filename).suffix.lower()
    if suffix not in FORMATS or not isinstance(raw,bytes) or not 0<len(raw)<=MAX_FILE:raise UnsupportedDocument("Supported synthetic formats: TXT, PDF, DOCX and XLSX, up to 256 KiB")
    try:
        if suffix==".txt":
            text=_check_text(raw.decode("utf-8"));out=[]
            for num,line in enumerate(text.splitlines(),1):_segments_add(out,line,f"Text line {num}")
        else:out={".pdf":_pdf,".docx":_docx,".xlsx":_xlsx}[suffix](raw)
    except UnsupportedDocument:raise
    except Exception as e:raise UnsupportedDocument("Unsupported or malformed synthetic document") from e
    if sum(len(i["text"]) for i in out)>MAX_TEXT:raise UnsupportedDocument("Extracted text limit")
    return {"format":suffix[1:],"segments":out}
_CHILD_MODE=False
def enable_child_parser(enabled=True):
    global _CHILD_MODE
    _CHILD_MODE=enabled is True
def parser_mode():return "bounded_child_process" if _CHILD_MODE else "bounded_in_process"
def parse_document(filename,raw):
    if not _CHILD_MODE:return _parse_document(filename,raw)
    if not isinstance(filename,str) or len(filename)>4000 or not isinstance(raw,bytes) or not 0<len(raw)<=MAX_FILE:raise UnsupportedDocument("Synthetic parser input limit")
    payload=json.dumps({"filename":filename,"data":base64.b64encode(raw).decode()}).encode()
    try:
        r=subprocess.run([sys.executable,"-I",str(Path(__file__).with_name("parser_worker.py"))],input=payload,capture_output=True,timeout=15,check=False)
        if r.returncode!=0 or len(r.stdout)>2*1024*1024:raise UnsupportedDocument("Child parser failed or exceeded output limit")
        result=json.loads(r.stdout)
        if "error" in result:raise UnsupportedDocument(str(result["error"])[:200])
        return result["result"]
    except UnsupportedDocument:raise
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:raise UnsupportedDocument("Child parser unavailable or timed out") from e
def preview_document(filename,raw):
    parsed=parse_document(filename,raw)
    return "\n".join(f"[{s['location']}] {s['text']}" for s in parsed["segments"])
def extract_document(filename,raw,rule):
    parsed=parse_document(filename,raw)
    fields=rule["fields"];labels={f["label"].strip().casefold():f["key"] for f in fields};matched={f["key"]:[] for f in fields}
    for seg in parsed["segments"]:
        if "pair" in seg:
            pair=seg["pair"];key=labels.get(pair["label"].strip().casefold());value=pair["value"].strip()
            if key is None or not value:continue
            matched[key].append({"value":value,"location":pair["valueLocation"],"labelLocation":pair["labelLocation"],"excerpt":pair["value"],**{k:pair[k] for k in ("valueType","rawValue","numberFormat") if k in pair}})
        else:
            line=seg["text"];left,sep,right=line.partition(":");key=labels.get(left.strip().casefold())
            if not sep or key is None or not right.strip():continue
            value=right.strip();start=len(left)+1+(len(right)-len(right.lstrip()))+1
            matched[key].append({"value":value,"location":seg["location"],"startColumn":start,"endColumn":start+len(value)-1,"excerpt":line})
    records=[]
    for f in fields:
        candidates=matched[f["key"]];distinct={c["value"] for c in candidates};state="missing" if not candidates else "present" if len(distinct)==1 else "ambiguous"
        records.append({"key":f["key"],"label":f["label"],"status":state,"value":candidates[0]["value"] if state=="present" else None,"citations":candidates})
    return {"criterionId":rule["criterionId"],"ruleId":rule["ruleId"],"method":METHOD,"format":parsed["format"],"status":"draft","scoringEligible":False,"fields":records,"counts":{k:sum(x["status"]==k for x in records) for k in ("present","missing","ambiguous")}}
