"""Bounded child process for fictional input parsing; not an OS sandbox."""
import base64,json,resource,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from document_parser import _parse_document,UnsupportedDocument
def main():
    try:
        resource.setrlimit(resource.RLIMIT_CPU,(8,8))
        raw=sys.stdin.buffer.read(400000)
        request=json.loads(raw)
        parsed=_parse_document(request["filename"],base64.b64decode(request["data"],validate=True))
        result=json.dumps({"result":parsed},ensure_ascii=False,separators=(",",":")).encode()
        if len(result)>2*1024*1024:raise UnsupportedDocument("Parser result limit")
        sys.stdout.buffer.write(result)
    except UnsupportedDocument as e:sys.stdout.write(json.dumps({"error":str(e)}))
    except Exception:sys.stdout.write(json.dumps({"error":"Child parser refused unsupported content"}))
if __name__=="__main__":main()
