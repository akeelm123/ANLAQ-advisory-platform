"""Synthetic-only local data plane reference; no server, client deployment or scoring."""
from __future__ import annotations
import hashlib, hmac, json, os, secrets, sqlite3, time, uuid
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from extraction import load_schema
from document_parser import parse_document,extract_document,UnsupportedDocument,METHOD as EXTRACTION_VERSION
from narrative import extract_narrative,NarrativeUnavailable
from interviews import InterviewWorkflow
from validation_workflow import ValidationWorkflow
from scoring import ScoringWorkflow

class Denied(Exception): pass
class Invalid(Exception): pass

ROLES={"contributor","assessor","reviewer","owner"}
MAX_FILE=256*1024
def ident(): return uuid.uuid4().hex
def digest(b): return hashlib.sha256(b).hexdigest()
def canonical(o): return json.dumps(o,sort_keys=True,separators=(",",":"),ensure_ascii=False)
def required(v,label):
    if not isinstance(v,str) or not v.strip() or len(v)>4000: raise Invalid(label+" required")
    return v.strip()
def password_hash(password,salt):
    return hashlib.scrypt(password.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32)

class DataPlane:
    def __init__(self,path,key,audit_key,register_path,spec_path,clock=time.time,enable_narrative=False,enable_pilot_scoring=False):
        self.enable_narrative=enable_narrative is True
        if len(key)!=32 or len(audit_key)!=32 or key==audit_key:raise Invalid("Independent 32-byte encryption and audit keys required")
        self.key=key; self.audit_key=audit_key; self.clock=clock; self.db=sqlite3.connect(path); self.db.row_factory=sqlite3.Row
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL, salt BLOB NOT NULL, password BLOB NOT NULL, active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE IF NOT EXISTS sessions(digest TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),expires REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS tenants(id TEXT PRIMARY KEY,name TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS assessments(id TEXT PRIMARY KEY,tenant_id TEXT NOT NULL REFERENCES tenants(id),title TEXT NOT NULL,scope TEXT NOT NULL,register_hash TEXT NOT NULL,spec_hash TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS membership(assessment_id TEXT NOT NULL REFERENCES assessments(id),user_id TEXT NOT NULL REFERENCES users(id),role TEXT NOT NULL,active INTEGER NOT NULL DEFAULT 1,PRIMARY KEY(assessment_id,user_id));
        CREATE TABLE IF NOT EXISTS docs(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),title TEXT NOT NULL,created_by TEXT NOT NULL REFERENCES users(id));
        CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY,doc_id TEXT NOT NULL REFERENCES docs(id),version INTEGER NOT NULL,filename TEXT NOT NULL,digest TEXT NOT NULL,nonce BLOB NOT NULL,ciphertext BLOB NOT NULL,created_by TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL,UNIQUE(doc_id,version));
        CREATE TABLE IF NOT EXISTS disposition(version_id TEXT PRIMARY KEY REFERENCES versions(id),status TEXT NOT NULL,actor TEXT NOT NULL REFERENCES users(id),reason TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS intake(version_id TEXT PRIMARY KEY REFERENCES versions(id),criterion TEXT NOT NULL,request_id TEXT NOT NULL,source_owner TEXT NOT NULL,period TEXT NOT NULL,source_version TEXT NOT NULL,locator TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS request_updates(id INTEGER PRIMARY KEY AUTOINCREMENT,assessment_id TEXT NOT NULL REFERENCES assessments(id),request_id TEXT NOT NULL,actor TEXT NOT NULL REFERENCES users(id),status TEXT NOT NULL,reason TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS findings(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),criterion TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),claim TEXT NOT NULL,evidence_class TEXT NOT NULL,strength TEXT NOT NULL,contradiction INTEGER NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS links(finding_id TEXT NOT NULL REFERENCES findings(id),version_id TEXT NOT NULL REFERENCES versions(id),request_id TEXT NOT NULL,locator TEXT NOT NULL,PRIMARY KEY(finding_id,version_id,request_id));
        CREATE TABLE IF NOT EXISTS reviews(id TEXT PRIMARY KEY,finding_id TEXT UNIQUE NOT NULL REFERENCES findings(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,reason TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS extraction_runs(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),version_id TEXT NOT NULL REFERENCES versions(id),criterion TEXT NOT NULL,actor TEXT NOT NULL REFERENCES users(id),schema_hash TEXT NOT NULL,method TEXT NOT NULL,nonce BLOB NOT NULL,ciphertext BLOB NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS extraction_reviews(id TEXT PRIMARY KEY,run_id TEXT UNIQUE NOT NULL REFERENCES extraction_runs(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,reason TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY,assessment_id TEXT NOT NULL,actor TEXT NOT NULL,action TEXT NOT NULL,record_id TEXT NOT NULL,time REAL NOT NULL,previous TEXT NOT NULL,mac TEXT NOT NULL);
        CREATE TRIGGER IF NOT EXISTS immutable_versions_update BEFORE UPDATE ON versions BEGIN SELECT RAISE(ABORT,'immutable source version'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_versions_delete BEFORE DELETE ON versions BEGIN SELECT RAISE(ABORT,'immutable source version'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_audit_update BEFORE UPDATE ON audit BEGIN SELECT RAISE(ABORT,'append only audit'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_audit_delete BEFORE DELETE ON audit BEGIN SELECT RAISE(ABORT,'append only audit'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_extraction_update BEFORE UPDATE ON extraction_runs BEGIN SELECT RAISE(ABORT,'immutable extraction'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_extraction_delete BEFORE DELETE ON extraction_runs BEGIN SELECT RAISE(ABORT,'immutable extraction'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_extraction_review_update BEFORE UPDATE ON extraction_reviews BEGIN SELECT RAISE(ABORT,'immutable extraction review'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_extraction_review_delete BEFORE DELETE ON extraction_reviews BEGIN SELECT RAISE(ABORT,'immutable extraction review'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_intake_update BEFORE UPDATE ON intake BEGIN SELECT RAISE(ABORT,'immutable intake'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_intake_delete BEFORE DELETE ON intake BEGIN SELECT RAISE(ABORT,'immutable intake'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_request_update BEFORE UPDATE ON request_updates BEGIN SELECT RAISE(ABORT,'immutable request event'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_request_delete BEFORE DELETE ON request_updates BEGIN SELECT RAISE(ABORT,'immutable request event'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_disposition_update BEFORE UPDATE ON disposition BEGIN SELECT RAISE(ABORT,'immutable disposition'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_disposition_delete BEFORE DELETE ON disposition BEGIN SELECT RAISE(ABORT,'immutable disposition'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_findings_update BEFORE UPDATE ON findings BEGIN SELECT RAISE(ABORT,'immutable finding'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_findings_delete BEFORE DELETE ON findings BEGIN SELECT RAISE(ABORT,'immutable finding'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_links_update BEFORE UPDATE ON links BEGIN SELECT RAISE(ABORT,'immutable link'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_links_delete BEFORE DELETE ON links BEGIN SELECT RAISE(ABORT,'immutable link'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_reviews_update BEFORE UPDATE ON reviews BEGIN SELECT RAISE(ABORT,'immutable review'); END;
        CREATE TRIGGER IF NOT EXISTS immutable_reviews_delete BEFORE DELETE ON reviews BEGIN SELECT RAISE(ABORT,'immutable review'); END;
        """)
        rb=Path(register_path).read_bytes(); sb=Path(spec_path).read_bytes()
        self.register_hash=digest(rb); self.spec_hash=digest(sb)
        # Fail closed on unapproved or changed methodology. Approval is versioned in repo.
        if self.register_hash!="f402011665fa4abd6405cc6c67384b4182564cc5e974761079c1588488420559" or self.spec_hash!="8d4e730b5ed3cf38fdb4dcd896fa21bc14bf38689babc24159a460980099b00c": raise Invalid("Methodology hash mismatch")
        reg=json.loads(rb);self.catalogue={r["id"]:r for r in reg["evidenceCatalogue"]};self.criteria=reg["criteria"]
        spec=json.loads(sb)
        self.rules={r["criterionId"]:r for r in spec["rules"]}
        self.mappings={c:set(r["primary"]+r["supplementary"]+r["conditional"]) for c,r in self.rules.items()}
        self.extraction_rules,self.extraction_schema_hash=load_schema(Path(__file__).with_name("extraction-schema.json"),sb)
        self.interviews=InterviewWorkflow(self,Invalid,Denied,required)
        self.validation=ValidationWorkflow(self,Invalid,Denied,required)
        self.scoring=ScoringWorkflow(self,reg,Invalid,Denied,required,enable_pilot_scoring)
    # Trusted local bootstrap only. No exposed self-service administrator endpoint.
    def bootstrap_user(self,username,password):
        username=required(username,"username")
        if not isinstance(password,str) or len(password)<12 or len(password)>256: raise Invalid("Synthetic password length 12–256")
        uid=ident();salt=secrets.token_bytes(16)
        with self.db:self.db.execute("INSERT INTO users(id,username,salt,password) VALUES (?,?,?,?)",(uid,username,salt,password_hash(password,salt)))
        return uid
    def bootstrap_assessment(self,tenant_name,title,scope):
        tid,aid=ident(),ident()
        with self.db:
            self.db.execute("INSERT INTO tenants VALUES (?,?)",(tid,required(tenant_name,"tenant")))
            self.db.execute("INSERT INTO assessments VALUES (?,?,?,?,?,?)",(aid,tid,required(title,"title"),required(scope,"scope"),self.register_hash,self.spec_hash))
        return aid
    def bootstrap_membership(self,assessment,user,role):
        if role not in ROLES:raise Invalid("Unknown role")
        with self.db:self.db.execute("INSERT INTO membership VALUES (?,?,?,1)",(assessment,user,role))
    def login(self,username,password):
        if not isinstance(username,str) or not isinstance(password,str) or len(password)>256:raise Denied("Invalid credentials")
        row=self.db.execute("SELECT * FROM users WHERE username=?",(username,)).fetchone()
        salt=row["salt"] if row else b"\x00"*16
        candidate=password_hash(password,salt)
        if not row or not hmac.compare_digest(candidate,row["password"]) or not row["active"]:raise Denied("Invalid credentials")
        token=secrets.token_urlsafe(32)
        with self.db:self.db.execute("INSERT INTO sessions VALUES (?,?,?)",(digest(token.encode()),row["id"],self.clock()+1800))
        return token
    def _session_user(self,token):
        if not isinstance(token,str):raise Denied("Access denied")
        row=self.db.execute("SELECT u.id,u.username FROM sessions s JOIN users u ON u.id=s.user_id WHERE s.digest=? AND s.expires>? AND u.active=1",(digest(token.encode()),self.clock())).fetchone()
        if not row:raise Denied("Access denied")
        return row
    def list_assessments(self,token):
        u=self._session_user(token)
        return [dict(r) for r in self.db.execute("SELECT a.id,a.title,a.scope,m.role FROM assessments a JOIN membership m ON a.id=m.assessment_id WHERE m.user_id=? AND m.active=1 AND a.register_hash=? AND a.spec_hash=? ORDER BY a.title",(u["id"],self.register_hash,self.spec_hash))]
    def logout(self,token):
        with self.db:self.db.execute("DELETE FROM sessions WHERE digest=?",(digest(token.encode()),))
    def _actor(self,token,assessment,roles):
        if not isinstance(token,str):raise Denied("Access denied")
        r=self.db.execute("""SELECT u.id,m.role,a.tenant_id,a.register_hash,a.spec_hash FROM sessions s JOIN users u ON u.id=s.user_id JOIN membership m ON m.user_id=u.id JOIN assessments a ON a.id=m.assessment_id WHERE s.digest=? AND s.expires>? AND u.active=1 AND m.active=1 AND m.assessment_id=?""",(digest(token.encode()),self.clock(),assessment)).fetchone()
        if not r or r["role"] not in roles or r["register_hash"]!=self.register_hash or r["spec_hash"]!=self.spec_hash:raise Denied("Access denied")
        return r
    def revoke_membership(self,token,assessment,user):
        with self.db:
            a=self._actor(token,assessment,{"owner"})
            if a["id"]==user:raise Denied("Cannot revoke own membership")
            changed=self.db.execute("UPDATE membership SET active=0 WHERE assessment_id=? AND user_id=? AND active=1",(assessment,user)).rowcount
            if changed!=1:raise Denied("Access denied")
            self._audit(assessment,a["id"],"membership revoked",user)
    def _audit(self,assessment,actor,action,record):
        last=self.db.execute("SELECT seq,mac FROM audit ORDER BY seq DESC LIMIT 1").fetchone()
        seq=(last["seq"]+1) if last else 1; previous=last["mac"] if last else "GENESIS"
        t=float(self.clock());body=[seq,assessment,actor,action,record,t,previous]
        mac=hmac.new(self.audit_key,canonical(body).encode(),hashlib.sha256).hexdigest()
        self.db.execute("INSERT INTO audit VALUES (?,?,?,?,?,?,?,?)",(*body,mac))
    def verify_audit(self):
        prior="GENESIS";expected=1
        for r in self.db.execute("SELECT * FROM audit ORDER BY seq"):
            body=[r["seq"],r["assessment_id"],r["actor"],r["action"],r["record_id"],r["time"],r["previous"]]
            if r["seq"]!=expected or r["previous"]!=prior or not hmac.compare_digest(r["mac"],hmac.new(self.audit_key,canonical(body).encode(),hashlib.sha256).hexdigest()):return False
            prior=r["mac"];expected+=1
        return True
    def _version(self,assessment,version):
        row=self.db.execute("""SELECT v.*,d.assessment_id,d.title,coalesce(p.status,'quarantined') AS status
          FROM versions v JOIN docs d ON d.id=v.doc_id LEFT JOIN disposition p ON p.version_id=v.id WHERE v.id=? AND d.assessment_id=?""",(version,assessment)).fetchone()
        if not row:raise Denied("Access denied")
        return row
    def _latest(self,row):
        return self.db.execute("SELECT max(version) FROM versions WHERE doc_id=?",(row["doc_id"],)).fetchone()[0]==row["version"]
    def upload(self,token,assessment,title,filename,data,document=None,intake=None):
        self._actor(token,assessment,{"contributor","assessor"})
        # Bounded synthetic format preflight only; not malware screening or parser isolation.
        if not isinstance(data,bytes) or not 0<len(data)<=MAX_FILE:raise Invalid("Synthetic file size")
        filename=required(filename,"filename");title=required(title,"title")
        if Path(filename).name!=filename or "/" in filename or "\\" in filename:raise Invalid("Invalid filename")
        try:parse_document(filename,data)
        except UnsupportedDocument as e:raise Invalid(str(e)) from e
        if intake is not None:
            if not isinstance(intake,dict) or intake.get("criterion") not in self.mappings or intake.get("requestId") not in self.mappings[intake["criterion"]]:raise Invalid("Approved criterion/request mapping required")
            intake={**intake,**{k:required(intake.get(k),k) for k in ["sourceOwner","period","sourceVersion","locator"]}}
        with self.db:
            a=self._actor(token,assessment,{"contributor","assessor"})
            if document:
                d=self.db.execute("SELECT * FROM docs WHERE id=? AND assessment_id=?",(document,assessment)).fetchone()
                if not d or (a["role"]=="contributor" and d["created_by"]!=a["id"]):raise Denied("Access denied")
                v=self.db.execute("SELECT max(version) FROM versions WHERE doc_id=?",(document,)).fetchone()[0]+1
            else:
                document=ident();v=1
                self.db.execute("INSERT INTO docs VALUES (?,?,?,?)",(document,assessment,title,a["id"]))
            vid=ident();dhash=digest(data);nonce=secrets.token_bytes(12);aad=canonical([a["tenant_id"],assessment,document,vid,v,dhash]).encode()
            ciphertext=AESGCM(self.key).encrypt(nonce,data,aad)
            self.db.execute("INSERT INTO versions VALUES (?,?,?,?,?,?,?,?,?)",(vid,document,v,filename,dhash,nonce,ciphertext,a["id"],self.clock()))
            if intake is not None:self.db.execute("INSERT INTO intake VALUES (?,?,?,?,?,?,?)",(vid,intake["criterion"],intake["requestId"],intake["sourceOwner"],intake["period"],intake["sourceVersion"],intake["locator"]))
            self._audit(assessment,a["id"],"source quarantined",vid)
            return {"documentId":document,"versionId":vid,"version":v,"sha256":dhash,"status":"quarantined"}
    def _read_bytes(self,a,assessment,v):
        aad=canonical([a["tenant_id"],assessment,v["doc_id"],v["id"],v["version"],v["digest"]]).encode()
        raw=AESGCM(self.key).decrypt(v["nonce"],v["ciphertext"],aad)
        if digest(raw)!=v["digest"]:raise Invalid("Integrity failure")
        return raw
    def inspect_quarantine(self,token,assessment,version):
        with self.db:
            a=self._actor(token,assessment,{"assessor"});v=self._version(assessment,version)
            if v["status"]!="quarantined" or v["created_by"]==a["id"]:raise Denied("Access denied")
            raw=self._read_bytes(a,assessment,v)
            self._audit(assessment,a["id"],"quarantine inspected",version)
            return raw
    def screen(self,token,assessment,version,decision,reason):
        if decision not in {"accepted","rejected"}:raise Invalid("Invalid disposition")
        reason=required(reason,"screening rationale")
        with self.db:
            a=self._actor(token,assessment,{"assessor"});v=self._version(assessment,version)
            if v["status"]!="quarantined":raise Invalid("Disposition immutable")
            if v["created_by"]==a["id"]:raise Denied("Independent screening required")
            if not self.db.execute("SELECT 1 FROM audit WHERE assessment_id=? AND actor=? AND action='quarantine inspected' AND record_id=?",(assessment,a["id"],version)).fetchone():raise Invalid("Inspect quarantined synthetic content first")
            self.db.execute("INSERT INTO disposition VALUES (?,?,?,?,?)",(version,decision,a["id"],reason,self.clock()))
            self._audit(assessment,a["id"],"synthetic screening "+decision,version)
    def download(self,token,assessment,version):
        with self.db:
            a=self._actor(token,assessment,ROLES);v=self._version(assessment,version)
            if v["status"]!="accepted" or (a["role"]=="contributor" and v["created_by"]!=a["id"]):raise Denied("Access denied")
            raw=self._read_bytes(a,assessment,v)
            self._audit(assessment,a["id"],"evidence downloaded",version)
            return raw
    def list_versions(self,token,assessment):
        a=self._actor(token,assessment,ROLES); own=a["role"]=="contributor"
        rows=self.db.execute("""SELECT v.id AS versionId,v.doc_id AS documentId,v.version,v.filename,v.digest AS sha256,d.title,coalesce(p.status,'quarantined') AS status,
        i.criterion,i.request_id AS requestId,i.source_owner AS sourceOwner,i.period,i.source_version AS sourceVersion,i.locator,v.created_by
        FROM versions v JOIN docs d ON v.doc_id=d.id LEFT JOIN disposition p ON p.version_id=v.id LEFT JOIN intake i ON i.version_id=v.id WHERE d.assessment_id=? ORDER BY v.created_at,v.version""",(assessment,))
        return [{**{k:r[k] for k in r.keys() if k!="created_by"},"own":r["created_by"]==a["id"]} for r in rows if not own or r["created_by"]==a["id"]]
    def mark_request(self,token,assessment,request_id,status,reason):
        if request_id not in self.catalogue or status not in {"requested","missing"}:raise Invalid("Invalid request update")
        reason=required(reason,"request rationale")
        with self.db:
            a=self._actor(token,assessment,{"assessor"})
            if any(r["id"]==request_id and r["status"]=="received" for r in self.catalogue_view(token,assessment)["requests"]):raise Invalid("Accepted current evidence exists; record a finding for quality or gaps")
            cur=self.db.execute("INSERT INTO request_updates(assessment_id,request_id,actor,status,reason,created_at) VALUES (?,?,?,?,?,?)",(assessment,request_id,a["id"],status,reason,self.clock()))
            self._audit(assessment,a["id"],"request "+status,str(cur.lastrowid))
    def catalogue_view(self,token,assessment):
        a=self._actor(token,assessment,ROLES)
        versions=self.list_versions(token,assessment)
        latest={}
        for v in versions:
            if v["documentId"] not in latest or v["version"]>latest[v["documentId"]]["version"]:latest[v["documentId"]]=v
        received={v["requestId"] for v in latest.values() if v["status"]=="accepted"}
        updates={}
        for r in self.db.execute("SELECT request_id,status FROM request_updates WHERE assessment_id=? ORDER BY id",(assessment,)):updates[r["request_id"]]=r["status"]
        requests=[{"id":r["id"],"title":r["title"],"dimension":r["dimension"],"status":"received" if r["id"] in received else updates.get(r["id"],"not requested"),"criteria":[k for k,ids in self.mappings.items() if r["id"] in ids]} for r in self.catalogue.values()]
        return {"criteria":[{"id":r["id"],"dimension":r["dimension"],"criterion":r["criterion"],"question":r["question"]} for r in self.criteria],"requests":requests,"catalogueCount":len(requests),"coverageVisibility":"own accepted versions only" if a["role"]=="contributor" else "assessment accepted current versions"}
    def list_findings(self,token,assessment):
        self._actor(token,assessment,{"assessor","reviewer","owner"})
        rows=list(self.db.execute("SELECT id,criterion,claim,evidence_class AS evidenceClass,strength,contradiction,created_at FROM findings WHERE assessment_id=? ORDER BY created_at",(assessment,)))
        return [{**dict(r),"state":self.review_state(token,assessment,r["id"]),"links":[dict(l) for l in self.db.execute("SELECT version_id AS versionId,request_id AS requestId,locator FROM links WHERE finding_id=?",(r["id"],))]} for r in rows]
    def draft_finding(self,token,assessment,criterion,claim,evidence_class,strength,contradiction,links):
        if criterion not in self.mappings or evidence_class not in {"E1","E2","E3","E4"} or strength not in {"Strong","Moderate","Weak","Not assessed"} or type(contradiction) is not bool:raise Invalid("Invalid finding metadata")
        claim=required(claim,"claim")
        if not isinstance(links,list) or (evidence_class in {"E1","E2","E3"} and not links):raise Invalid("Evidence links required")
        with self.db:
            a=self._actor(token,assessment,{"assessor"}); fid=ident()
            self.db.execute("INSERT INTO findings VALUES (?,?,?,?,?,?,?,?,?)",(fid,assessment,criterion,a["id"],claim,evidence_class,strength,int(contradiction),self.clock()))
            for link in links:
                if link["requestId"] not in self.mappings[criterion]:raise Invalid("Unmapped request")
                v=self._version(assessment,link["versionId"])
                if v["status"]!="accepted" or not self._latest(v):raise Invalid("Only accepted current source versions")
                intake=self.db.execute("SELECT request_id FROM intake WHERE version_id=?",(v["id"],)).fetchone()
                if intake and intake["request_id"]!=link["requestId"]:raise Invalid("Finding request must match source intake record")
                self.db.execute("INSERT INTO links VALUES (?,?,?,?)",(fid,v["id"],link["requestId"],required(link["locator"],"precise locator")))
            self._audit(assessment,a["id"],"finding drafted",fid)
            return fid
    def review(self,token,assessment,finding,decision,reason,confirmed=False):
        if decision not in {"accept","return"}:raise Invalid("Invalid review decision")
        reason=required(reason,"review rationale")
        with self.db:
            a=self._actor(token,assessment,{"reviewer"})
            f=self.db.execute("SELECT * FROM findings WHERE id=? AND assessment_id=?",(finding,assessment)).fetchone()
            if not f or f["author"]==a["id"]:raise Denied("Independent review required")
            if self.db.execute("SELECT 1 FROM reviews WHERE finding_id=?",(finding,)).fetchone():raise Invalid("Already reviewed; draft new revision")
            links=list(self.db.execute("SELECT * FROM links WHERE finding_id=?",(finding,)))
            if decision=="accept":
                if f["evidence_class"] not in {"E1","E2"} or f["strength"]=="Not assessed" or f["contradiction"] or confirmed is not True:raise Invalid("Sufficiency or review confirmation outstanding")
                vs=[self._version(assessment,l["version_id"]) for l in links]
                if not vs or any(v["status"]!="accepted" or not self._latest(v) for v in vs):raise Invalid("Evidence superseded or unavailable")
                if f["evidence_class"]=="E2" and (len({v["digest"] for v in vs})<2 or len({v["created_by"] for v in vs})<2):raise Invalid("Distinct source bytes and contributors required; reviewer confirms actual independence")
                r=self.rules[f["criterion"]]
                if not any(l["request_id"] in r["primary"] for l in links):raise Invalid("Primary evidence required; alternate approval workflow not implemented")
                if r["conditional"]:raise Invalid("Conditional applicability review workflow outstanding; return for follow-up")
            rid=ident();self.db.execute("INSERT INTO reviews VALUES (?,?,?,?,?,?)",(rid,finding,a["id"],decision,reason,self.clock()))
            self._audit(assessment,a["id"],"review "+decision,rid)
            return rid
    def review_state(self,token,assessment,finding):
        a=self._actor(token,assessment,{"assessor","reviewer","owner"})
        f=self.db.execute("SELECT id FROM findings WHERE id=? AND assessment_id=?",(finding,assessment)).fetchone()
        if not f:raise Denied("Access denied")
        if any(not self._latest(self._version(assessment,l["version_id"])) for l in self.db.execute("SELECT version_id FROM links WHERE finding_id=?",(finding,))):return "superseded"
        r=self.db.execute("SELECT decision FROM reviews WHERE finding_id=?",(finding,)).fetchone()
        return r["decision"] if r else "draft"
    def run_extraction(self,token,assessment,version,criterion,mode="labelled"):
        if mode not in {"labelled","narrative"}:raise Invalid("Unknown extraction mode")
        if mode=="narrative" and not self.enable_narrative:raise Invalid("Local model disabled; synthetic opt-in required")
        if criterion not in self.extraction_rules:raise Invalid("Unknown extraction criterion")
        with self.db:
            a=self._actor(token,assessment,{"assessor"})
            v=self._version(assessment,version)
            if v["status"]!="accepted" or not self._latest(v):raise Invalid("Extraction requires accepted current source version")
            intake=self.db.execute("SELECT request_id FROM intake WHERE version_id=?",(version,)).fetchone()
            if not intake or intake["request_id"] not in self.mappings[criterion]:raise Invalid("Source request must be mapped to selected criterion")
            raw=self._read_bytes(a,assessment,v)
            try:
                result=extract_narrative(v["filename"],raw,self.extraction_rules[criterion]) if mode=="narrative" else extract_document(v["filename"],raw,self.extraction_rules[criterion])
            except (UnsupportedDocument,NarrativeUnavailable) as e:raise Invalid(str(e)) from e
            method=result["method"]
            rid=ident();nonce=secrets.token_bytes(12)
            aad=canonical([assessment,rid,version,criterion,self.extraction_schema_hash,method]).encode()
            encrypted=AESGCM(self.key).encrypt(nonce,canonical(result).encode(),aad)
            self.db.execute("INSERT INTO extraction_runs VALUES (?,?,?,?,?,?,?,?,?,?)",(rid,assessment,version,criterion,a["id"],self.extraction_schema_hash,method,nonce,encrypted,self.clock()))
            self._audit(assessment,a["id"],"draft extraction created",rid)
            return rid
    def _extraction_payload(self,row):
        aad=canonical([row["assessment_id"],row["id"],row["version_id"],row["criterion"],row["schema_hash"],row["method"]]).encode()
        return json.loads(AESGCM(self.key).decrypt(row["nonce"],row["ciphertext"],aad))
    def list_extractions(self,token,assessment):
        self._actor(token,assessment,{"assessor","reviewer","owner"})
        out=[]
        for row in self.db.execute("SELECT * FROM extraction_runs WHERE assessment_id=? ORDER BY created_at",(assessment,)):
            v=self._version(assessment,row["version_id"]);p=self._extraction_payload(row)
            review=self.db.execute("SELECT decision,reason FROM extraction_reviews WHERE run_id=?",(row["id"],)).fetchone()
            stale=not self._latest(v)
            out.append({"id":row["id"],"versionId":v["id"],"sourceTitle":v["title"],"sourceSha256":v["digest"],"schemaSha256":row["schema_hash"],"criterionId":row["criterion"],"method":row["method"],"state":"superseded" if stale else review["decision"] if review else "draft","reviewReason":review["reason"] if review else None,"result":p})
        return out
    def review_extraction(self,token,assessment,run,decision,reason,confirmed=False):
        if decision not in {"accept","return"}:raise Invalid("Invalid extraction review decision")
        reason=required(reason,"review rationale")
        with self.db:
            a=self._actor(token,assessment,{"reviewer"})
            r=self.db.execute("SELECT * FROM extraction_runs WHERE id=? AND assessment_id=?",(run,assessment)).fetchone()
            if not r or r["actor"]==a["id"]:raise Denied("Independent extraction review required")
            if self.db.execute("SELECT 1 FROM extraction_reviews WHERE run_id=?",(run,)).fetchone():raise Invalid("Extraction already reviewed")
            v=self._version(assessment,r["version_id"])
            if decision=="accept":
                if not self._latest(v) or v["status"]!="accepted":raise Invalid("Source superseded or unavailable")
                result=self._extraction_payload(r)
                if result["counts"]["missing"] or result["counts"]["ambiguous"] or result.get("unresolvedRejectedProposals",result.get("rejectedProposals",0)):raise Invalid("Missing, ambiguous or rejected proposals; return for follow-up")
                if confirmed is not True or not self.db.execute("SELECT 1 FROM audit WHERE assessment_id=? AND actor=? AND action='evidence downloaded' AND record_id=?",(assessment,a["id"],v["id"])).fetchone():raise Invalid("Independent source preview and confirmation required")
            rid=ident()
            self.db.execute("INSERT INTO extraction_reviews VALUES (?,?,?,?,?,?)",(rid,run,a["id"],decision,reason,self.clock()))
            self._audit(assessment,a["id"],"extraction review "+decision,rid)
            return rid
    def release(self,token,assessment):
        self._actor(token,assessment,{"owner"})
        raise Denied("Scoring, executive release, real-client processing and deployment locked")
    def close(self):self.db.close()
