"""Loopback-only synthetic API and browser workbench. Not a deployable server."""
from __future__ import annotations
import argparse,base64,binascii,json,os,secrets,tempfile,signal
from http.server import BaseHTTPRequestHandler,HTTPServer
from pathlib import Path
from data_plane import DataPlane,Denied,Invalid
from document_parser import preview_document

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
REGISTER=Path(os.environ.get("TCI_REGISTER",ROOT/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
STATIC={"/":("index.html","text/html; charset=utf-8"),"/app.js":("app.js","text/javascript; charset=utf-8"),"/style.css":("style.css","text/css; charset=utf-8"),"/logo.svg":("logo.svg","image/svg+xml")}
MAX_BODY=380000

class Handler(BaseHTTPRequestHandler):
    server_version="TCI-Synthetic"
    sys_version=""
    def log_message(self,*args):pass # Do not log URLs, credentials, document data or tokens.
    def setup(self):
        super().setup();self.connection.settimeout(10)
    @property
    def dp(self):return self.server.dp
    @property
    def origin(self):return f"http://127.0.0.1:{self.server.server_port}"
    def headers_for(self,status,content_type,size):
        self.send_response(status)
        self.send_header("Content-Type",content_type);self.send_header("Content-Length",str(size))
        self.send_header("Cache-Control","no-store");self.send_header("X-Content-Type-Options","nosniff");self.send_header("Referrer-Policy","no-referrer")
        self.send_header("Content-Security-Policy","default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
    def payload(self,status,data):
        b=json.dumps(data,ensure_ascii=False,separators=(",",":")).encode();self.headers_for(status,"application/json; charset=utf-8",len(b));self.wfile.write(b)
    def host_ok(self):return self.headers.get("Host")==f"127.0.0.1:{self.server.server_port}"
    def token(self):
        auth=self.headers.get("Authorization","")
        if not auth.startswith("Bearer ") or not 10<len(auth)<200:raise Denied("Access denied")
        return auth[7:]
    def body(self):
        if self.headers.get("Content-Type","").split(";")[0].strip()!="application/json":raise Invalid("JSON required")
        try:n=int(self.headers.get("Content-Length","-1"))
        except ValueError:raise Invalid("Invalid request length")
        if not 0<n<=MAX_BODY:raise Invalid("Request too large or empty")
        data=json.loads(self.rfile.read(n))
        if not isinstance(data,dict):raise Invalid("JSON object required")
        return data
    def execute(self,method):
        if not self.host_ok():return self.payload(403,{"error":"Access denied"})
        try:
            if method=="GET" and self.path in STATIC:
                fname,ctype=STATIC[self.path];data=(HERE/fname).read_bytes()
                self.headers_for(200,ctype,len(data));self.wfile.write(data);return
            if method=="POST":
                if self.headers.get("Origin")!=self.origin:raise Denied("Origin denied")
                data=self.body()
            else:data={}
            if self.path=="/api/login" and method=="POST":
                # Return random ephemeral bearer only; no browser persistence.
                session=self.dp.login(data["username"],data["password"]);return self.payload(200,{"token":session})
            token=self.token()
            if self.path=="/api/logout" and method=="POST":
                self.dp._session_user(token);self.dp.logout(token);return self.payload(200,{"ok":True})
            if self.path=="/api/assessments" and method=="GET":return self.payload(200,{"assessments":self.dp.list_assessments(token)})
            parts=self.path.split("/")
            if len(parts)!=5 or parts[:3]!=["","api","assessments"]:return self.payload(404,{"error":"Unknown route"})
            aid,action=parts[3:]
            # All operations, including viewing metadata, must first check assessment membership.
            role=self.dp._actor(token,aid,{"contributor","assessor","reviewer","owner"})["role"]
            if method=="GET" and action=="dashboard":
                return self.payload(200,{"role":role,"catalogue":self.dp.catalogue_view(token,aid),"versions":self.dp.list_versions(token,aid),"findings":[] if role=="contributor" else self.dp.list_findings(token,aid),"extractions":[] if role=="contributor" else self.dp.list_extractions(token,aid),"narrativeEnabled":self.dp.enable_narrative,"interviews":None if role=="contributor" else self.dp.interviews.view(token,aid),"validation":None if role=="contributor" else self.dp.validation.view(token,aid),"pilotScoring":None if role=="contributor" else self.dp.scoring.view(token,aid),"executive":None if role=="contributor" else self.dp.executive.view(token,aid),"reassessment":None if role=="contributor" else self.dp.reassessment.view(token,aid),"auroraPilot":self.server.aurora_summary if role!="contributor" and aid==self.server.aurora_assessment else None,"releaseLocked":True})
            if method!="POST":return self.payload(404,{"error":"Unknown route"})
            if action=="upload":
                try:raw=base64.b64decode(data["contentBase64"],validate=True)
                except (binascii.Error,TypeError):raise Invalid("Invalid file data")
                record=self.dp.upload(token,aid,data["title"],data["filename"],raw,data.get("documentId") or None,data["intake"])
                return self.payload(201,{"record":record})
            if action=="request":
                self.dp.mark_request(token,aid,data["requestId"],data["status"],data["reason"])
            elif action=="inspect":
                raw=self.dp.inspect_quarantine(token,aid,data["versionId"]);v=self.dp._version(aid,data["versionId"])
                return self.payload(200,{"text":raw.decode("utf-8") if v["filename"].lower().endswith(".txt") else preview_document(v["filename"],raw)})
            elif action=="screen":self.dp.screen(token,aid,data["versionId"],data["decision"],data["reason"])
            elif action=="preview":
                raw=self.dp.download(token,aid,data["versionId"]);v=self.dp._version(aid,data["versionId"])
                return self.payload(200,{"text":raw.decode("utf-8") if v["filename"].lower().endswith(".txt") else preview_document(v["filename"],raw)})
            elif action=="finding":
                fid=self.dp.draft_finding(token,aid,data["criterion"],data["claim"],data["evidenceClass"],data["strength"],data["contradiction"],data["links"]);return self.payload(201,{"findingId":fid})
            elif action=="review":
                self.dp.review(token,aid,data["findingId"],data["decision"],data["reason"],data.get("confirmed",False))
            elif action=="extract":
                return self.payload(201,{"runId":self.dp.run_extraction(token,aid,data["versionId"],data["criterion"],data.get("mode","labelled"))})
            elif action=="extraction-review":
                self.dp.review_extraction(token,aid,data["runId"],data["decision"],data["reason"],data.get("confirmed",False))
            elif action=="interview-start":
                return self.payload(201,{"sessionId":self.dp.interviews.start(token,aid,data["persona"],data["stakeholderRef"],data["role"],data["scope"])})
            elif action=="interview-response":
                return self.payload(201,{"claimId":self.dp.interviews.record(token,aid,data["sessionId"],data["questionId"],data["status"],data.get("verbatim",""),data["interpretation"],data.get("flags",[]),data.get("links",[]))})
            elif action=="interview-conflict":
                return self.payload(201,{"conflictId":self.dp.interviews.conflict(token,aid,data["claimA"],data["claimB"],data["topic"],data["material"])})
            elif action=="interview-model-wording":
                return self.payload(201,self.dp.interviews.draft_model_wording(token,aid,data["claimId"]))
            elif action=="interview-followup":
                return self.payload(201,{"followUpId":self.dp.interviews.record_followup(token,aid,data["claimId"],data["triggerId"],data["question"],data.get("proposalId"))})
            elif action=="interview-answer":
                self.dp.interviews.answer(token,aid,data["followUpId"],data["status"],data.get("verbatim",""))
            elif action=="interview-review":
                self.dp.interviews.review_capture(token,aid,data["claimId"],data["decision"],data["reason"],data.get("confirmed",False))
            elif action=="validation-draft":
                return self.payload(201,{"draftId":self.dp.validation.draft(token,aid,data["criterion"],data)})
            elif action=="validation-review":
                return self.payload(201,{"reviewId":self.dp.validation.review(token,aid,data["draftId"],data["decision"],data["reason"],data["controls"])})
            elif action=="validation-conflict-resolution":
                return self.payload(201,{"resolutionId":self.dp.validation.conflict_resolution(token,aid,data["conflictId"],data["reason"],data["refs"],data.get("confirmed",False))})
            elif action=="pilot-score-draft":
                return self.payload(201,{"scoreId":self.dp.scoring.draft(token,aid,data["criterion"],data["validationId"],data["score"],data["rationale"],data["operating"],data["redFlag"])})
            elif action=="pilot-score-review":
                return self.payload(201,{"reviewId":self.dp.scoring.review(token,aid,data["scoreId"],data["decision"],data["reason"],data["confirmed"],data["operatingConfirmed"])})
            elif action=="executive-draft":
                return self.payload(201,{"briefId":self.dp.executive.draft(token,aid,data)})
            elif action=="executive-review":
                return self.payload(201,{"reviewId":self.dp.executive.review(token,aid,data["briefId"],data["decision"],data["reason"],data["confirmed"])})
            elif action=="executive-direction":
                return self.payload(201,{"directionId":self.dp.executive.direction(token,aid,data["briefId"],data["direction"],data["reason"],data["conditions"],data["confirmed"])})
            elif action=="reassessment-capture":
                return self.payload(201,{"snapshotId":self.dp.reassessment.capture(token,aid,data["periodStart"],data["periodEnd"],data["label"],data["basis"])})
            elif action=="reassessment-snapshot-review":
                return self.payload(201,{"reviewId":self.dp.reassessment.review_snapshot(token,aid,data["snapshotId"],data["decision"],data["reason"],data["confirmed"])})
            elif action=="reassessment-compare":
                return self.payload(201,{"comparisonId":self.dp.reassessment.compare(token,aid,data["baselineId"],data["followUpId"],data["rationale"],data["confirmed"],data["actions"])})
            elif action=="reassessment-comparison-review":
                return self.payload(201,{"reviewId":self.dp.reassessment.review_comparison(token,aid,data["comparisonId"],data["decision"],data["reason"],data["confirmed"])})
            elif action=="release":self.dp.release(token,aid)
            else:return self.payload(404,{"error":"Unknown route"})
            return self.payload(200,{"ok":True})
        except Denied:return self.payload(403,{"error":"Access denied or release gate locked"})
        except (Invalid,KeyError,TypeError,ValueError,AttributeError) as e:
            return self.payload(400,{"error":str(e) if isinstance(e,Invalid) else "Invalid request"})
        except Exception:return self.payload(500,{"error":"Request failed; no client details logged"})
    def do_GET(self):self.execute("GET")
    def do_POST(self):self.execute("POST")

def main():
    def stop(_signum,_frame):raise KeyboardInterrupt
    signal.signal(signal.SIGTERM,stop)
    p=argparse.ArgumentParser(description="Synthetic-only loopback demo");p.add_argument("--port",type=int,default=8765);p.add_argument("--enable-local-model",action="store_true",help="Synthetic narrative local model opt-in");p.add_argument("--enable-pilot-scoring",action="store_true",help="Synthetic calibration only; never production scoring");p.add_argument("--aurora-pilot-workbook",help="Opt-in hash-pinned fictional workbook test; scripted synthetic review actions");args=p.parse_args()
    with tempfile.TemporaryDirectory(prefix="tci-synthetic-") as tmp:
        dp=DataPlane(Path(tmp)/"synthetic.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),REGISTER,SPEC,enable_narrative=args.enable_local_model,enable_pilot_scoring=args.enable_pilot_scoring)
        try:
            aid=dp.bootstrap_assessment("Synthetic tenant","Aurora fictional workbook dry run" if args.aurora_pilot_workbook else "Synthetic transformation","Synthetic investment decision only; no real client data.")
            passwords={}
            for name,role in [("contributor","contributor"),("assessor","assessor"),("reviewer","reviewer"),("owner","owner")]:
                pw=secrets.token_urlsafe(24);uid=dp.bootstrap_user(name,pw);dp.bootstrap_membership(aid,uid,role);passwords[name]=pw
            other=dp.bootstrap_assessment("Separate synthetic tenant","Separate assessment","Isolated synthetic assessment.")
            pw=secrets.token_urlsafe(24);uid=dp.bootstrap_user("other",pw);dp.bootstrap_membership(other,uid,"assessor");passwords["other"]=pw
            aurora_summary=None
            if args.aurora_pilot_workbook:
                from aurora_pilot import source_case
                tokens={role:dp.login(role,passwords[role]) for role in ("contributor","assessor","reviewer","owner")}
                aurora_summary=source_case(dp,aid,tokens,args.aurora_pilot_workbook)
                for token in tokens.values():dp.logout(token)
            with HTTPServer(("127.0.0.1",args.port),Handler) as server:
                server.dp=dp;server.aurora_summary=aurora_summary;server.aurora_assessment=aid
                # One-time local console credentials, randomly generated for this ephemeral session.
                print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}","users":passwords,"assessment":aid,"otherAssessment":other}),flush=True)
                try:server.serve_forever()
                except KeyboardInterrupt:pass
        finally:dp.close()
if __name__=="__main__":main()
