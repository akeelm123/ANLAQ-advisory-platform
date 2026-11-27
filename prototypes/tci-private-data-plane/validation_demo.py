"""Document-backed mock validation preview. No Aurora workbook or actual client records."""
import argparse,json,secrets,signal
from pathlib import Path
from http.server import HTTPServer
from data_plane import DataPlane
from serve import Handler,REGISTER,SPEC

HERE=Path(__file__).resolve().parent
QUESTIONS=("Q01","Q05","Q09","Q13","Q17","Q21","Q25")

def seed_validation_demo(dp,aid,t):
    fixtures={f["criterionId"]:f for f in json.loads((HERE/"golden-fixtures.json").read_text())["fixtures"]}
    def source(q,request,text,role,owner):
        v=dp.upload(t[role],aid,"MOCK evidence "+q+" / "+request,q+".txt",text.encode(),intake={"criterion":q,"requestId":request,"sourceOwner":owner,"period":"Fictional test period","sourceVersion":"1","locator":"Text source"});vid=v["versionId"]
        dp.inspect_quarantine(t["assessor"],aid,vid);dp.screen(t["assessor"],aid,vid,"accepted","Scripted mock intake screening")
        dp.download(t["reviewer"],aid,vid);return vid
    for q in QUESTIONS:
        f=fixtures[q];request=f["requestId"];vid=source(q,request,f["text"],"contributor","Mock primary source owner")
        run=dp.run_extraction(t["assessor"],aid,vid,q)
        dp.review_extraction(t["reviewer"],aid,run,"accept","Scripted exact-field mock extraction review",True)
        refs=[{"versionId":vid,"requestId":request,"locator":"Text line "+str(e["line"]),"quote":e["excerpt"]} for e in f["expected"]]
        adverse=q in ("Q13","Q25");eclass="E1"
        if q=="Q25":
            extra=dp.rules[q]["supplementary"][0]
            text="MOCK corroborating source — not an Aurora document\nFictional independent source owner confirms mock shortfall.\n"
            v2=source(q,extra,text,"contributor2","Mock separate corroborating source owner")
            refs.append({"versionId":v2,"requestId":extra,"locator":"Text line 2","quote":"Fictional independent source owner confirms mock shortfall."});eclass="E2"
        body={"applicability":"applicable","condition":"not_met" if adverse else "met","evidenceClass":eclass,"strength":"Strong","fieldsVerified":True,"comparable":True,"materialityReviewed":True,"requiresCorroboration":eclass=="E2","documentaryConflict":False,"claim":"MOCK fixture — scripted supported adverse condition" if adverse else "MOCK fixture — scripted supported met condition","rationale":"Test-only human-role flags and exact source citations; not a real semantic judgement or Aurora result","owner":"Fictional source owner","followUp":"Review real evidence only under separate approval","conditionalApplies":False,"conditionalRationale":"Mock scope, no AI condition","refs":refs,"claimIds":[]}
        id=dp.validation.draft(t["assessor"],aid,q,body)
        dp.validation.review(t["reviewer"],aid,id,"accept","Scripted independent mock evidence review; inspect exact quotes below",{"confirmed":True,"independenceConfirmed":True})
    # Another criterion is not validated, demonstrating that evidence receipt alone is insufficient.
    f=fixtures["Q03"];source("Q03",f["requestId"],f["text"],"contributor","Mock primary source owner")
    dp.validation.draft(t["assessor"],aid,"Q03",{"applicability":"applicable","condition":"unknown","evidenceClass":"E4","strength":"Not assessed","fieldsVerified":False,"comparable":False,"materialityReviewed":False,"requiresCorroboration":False,"documentaryConflict":False,"claim":"MOCK receipt alone — evidence not yet linked or reviewed","rationale":"Accepted source exists but precision and support not yet reviewed","owner":"Fictional assessment owner","followUp":"Link exact source citations and review","conditionalApplies":None,"refs":[],"claimIds":[]})

def main():
    p=argparse.ArgumentParser(description="Fictional document-backed validation demonstration only");p.add_argument("--port",type=int,default=8767);args=p.parse_args()
    with DataPlaneContext() as dp:
      aid=dp.bootstrap_assessment("Mock demonstration tenant","MOCK document-backed validation — NOT Aurora","Scripted structural example only; no actual client records")
      passwords={};tokens={}
      for name,role in [("contributor","contributor"),("contributor2","contributor"),("assessor","assessor"),("reviewer","reviewer"),("owner","owner")]:
        pw=secrets.token_urlsafe(24);uid=dp.bootstrap_user(name,pw);dp.bootstrap_membership(aid,uid,role);passwords[name]=pw;tokens[name]=dp.login(name,pw)
      seed_validation_demo(dp,aid,tokens)
      for t in tokens.values():dp.logout(t)
      def stop(*_):raise KeyboardInterrupt
      signal.signal(signal.SIGTERM,stop)
      with HTTPServer(("127.0.0.1",args.port),Handler) as server:
        server.dp=dp;server.aurora_summary=None;server.aurora_assessment=None
        print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}","users":passwords}),flush=True)
        try:server.serve_forever()
        except KeyboardInterrupt:pass

class DataPlaneContext:
    def __enter__(self):
        self.dp=DataPlane(":memory:",secrets.token_bytes(32),secrets.token_bytes(32),REGISTER,SPEC);return self.dp
    def __exit__(self,*_):self.dp.close()
if __name__=="__main__":main()
