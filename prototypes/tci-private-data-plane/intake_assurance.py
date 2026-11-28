"""Synthetic intake assurance records and optional installed malware-scanner adapter."""
import hashlib,shutil,subprocess,uuid

METHOD="0.9.4-alpha.1"
class ScanUnavailable(ValueError):pass

def scanner_status():
    return "available" if shutil.which("clamscan") else "unavailable"

def scan_installed(raw):
    exe=shutil.which("clamscan")
    if not exe:return {"status":"unavailable","method":"ClamAV not installed"}
    try:
        version=subprocess.run([exe,"--version"],capture_output=True,timeout=5,check=False)
        if version.returncode!=0:return {"status":"unavailable","method":"ClamAV version unavailable"}
        # Feed bytes on stdin; no document file, no external service, no raw scanner output retained.
        r=subprocess.run([exe,"--no-summary","-"],input=raw,capture_output=True,timeout=30,check=False)
        label=version.stdout.decode("utf-8","replace").strip().splitlines()[0][:160]
        return {"status":"clean" if r.returncode==0 else "detected" if r.returncode==1 else "unavailable","method":label}
    except (OSError,subprocess.SubprocessError,IndexError):return {"status":"unavailable","method":"ClamAV execution unavailable"}

class IntakeAssurance:
    def __init__(self,dp,invalid):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.require_scan=False
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS intake_assurance(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),actor TEXT NOT NULL REFERENCES users(id),version_id TEXT REFERENCES versions(id),digest TEXT NOT NULL,scan_status TEXT NOT NULL,scan_method TEXT NOT NULL,parser_mode TEXT NOT NULL,outcome TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TRIGGER IF NOT EXISTS intake_assurance_no_change BEFORE UPDATE ON intake_assurance BEGIN SELECT RAISE(ABORT,'immutable intake assurance'); END;
        CREATE TRIGGER IF NOT EXISTS intake_assurance_no_delete BEFORE DELETE ON intake_assurance BEGIN SELECT RAISE(ABORT,'immutable intake assurance'); END;
        """)
    def check(self,raw):
        if not self.require_scan:return {"status":"not_scanned","method":"Synthetic format-only policy"}
        return scan_installed(raw)
    def record(self,aid,actor,raw,result,parser_mode,outcome,version=None):
        id=uuid.uuid4().hex
        self.db.execute("INSERT INTO intake_assurance VALUES (?,?,?,?,?,?,?,?,?,?)",(id,aid,actor,version,hashlib.sha256(raw).hexdigest(),result["status"],result["method"],parser_mode,outcome,self.dp.clock()))
        self.dp._audit(aid,actor,"intake assurance "+outcome,id)
        return id
    def require_clean(self,aid,version,digest):
        if self.require_scan and not self.db.execute("SELECT 1 FROM intake_assurance WHERE assessment_id=? AND version_id=? AND digest=? AND scan_status='clean' AND outcome='quarantined'",(aid,version,digest)).fetchone():
            raise self.Invalid("Strict intake requires a recorded clean scan of this exact source version")
    def view(self,token,aid):
        self.dp._actor(token,aid,{"assessor","reviewer","owner"})
        return {"method":METHOD,"policy":"require_clean_scan" if self.require_scan else "synthetic_format_only","scanner":scanner_status(),"records":[dict(r) for r in self.db.execute("SELECT id,version_id AS versionId,digest,scan_status AS scanStatus,scan_method AS scanMethod,parser_mode AS parserMode,outcome FROM intake_assurance WHERE assessment_id=? ORDER BY created_at,rowid",(aid,))]}
