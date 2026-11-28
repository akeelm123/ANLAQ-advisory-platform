"""Dashboard-only child parser limits. No global change to the original workbench."""
import base64,json,resource,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import document_parser as parser
from dashboard_parser import MAX_DASHBOARD_FILE,MAX_DASHBOARD_BODY,MAX_DASHBOARD_RESULT
def main():
    try:
        resource.setrlimit(resource.RLIMIT_CPU,(10,10))
        raw=sys.stdin.buffer.read(MAX_DASHBOARD_BODY+1)
        if len(raw)>MAX_DASHBOARD_BODY:raise parser.UnsupportedDocument("Dashboard parser input limit")
        request=json.loads(raw)
        parser.MAX_FILE=MAX_DASHBOARD_FILE;parser.MAX_TEXT=512*1024
        # Keep archive expansion, segment, PDF page and spreadsheet limits unchanged.
        parsed=parser._parse_document(request["filename"],base64.b64decode(request["data"],validate=True))
        result=json.dumps({"result":parsed},ensure_ascii=False,separators=(",",":")).encode()
        if len(result)>MAX_DASHBOARD_RESULT:raise parser.UnsupportedDocument("Dashboard parser output limit")
        sys.stdout.buffer.write(result)
    except parser.UnsupportedDocument as e:sys.stdout.write(json.dumps({"error":str(e).replace("256 KiB","1 MiB")}))
    except Exception:sys.stdout.write(json.dumps({"error":"Dashboard parser refused unsupported content"}))
if __name__=="__main__":main()
