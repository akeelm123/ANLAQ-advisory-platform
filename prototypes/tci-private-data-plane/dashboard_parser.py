"""Dedicated bounded parser for fictional dashboard UAT, not the original workbench."""
import base64,json,subprocess,sys
from pathlib import Path
from document_parser import UnsupportedDocument
MAX_DASHBOARD_FILE=1024*1024
MAX_DASHBOARD_BODY=1_450_000
MAX_DASHBOARD_RESULT=4*1024*1024
def parse_dashboard_document(filename,raw):
    if not isinstance(filename,str) or len(filename)>250 or not isinstance(raw,bytes) or not 0<len(raw)<=MAX_DASHBOARD_FILE:raise UnsupportedDocument("Dashboard preview file limit is 1 MiB")
    payload=json.dumps({"filename":filename,"data":base64.b64encode(raw).decode()}).encode()
    try:
        p=subprocess.run([sys.executable,"-I",str(Path(__file__).with_name("dashboard_parser_worker.py"))],input=payload,capture_output=True,timeout=20,check=False)
        if p.returncode!=0 or len(p.stdout)>MAX_DASHBOARD_RESULT:raise UnsupportedDocument("Dashboard parser refused or exceeded resource limit")
        result=json.loads(p.stdout)
        if "error" in result:raise UnsupportedDocument(str(result["error"])[:200])
        return result["result"]
    except UnsupportedDocument:raise
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as e:raise UnsupportedDocument("Dashboard parser unavailable or timed out") from e
