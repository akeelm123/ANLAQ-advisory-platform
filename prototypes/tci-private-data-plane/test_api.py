"""Synthetic loopback integration tests. No credentials are printed or persisted."""
import base64,json,subprocess,sys,unittest,urllib.request,urllib.error
from pathlib import Path
HERE=Path(__file__).resolve().parent
class APITest(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.proc=subprocess.Popen([sys.executable,str(HERE/"serve.py"),"--port","0"],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    line=cls.proc.stdout.readline()
    if not line:raise RuntimeError("Synthetic server did not start")
    cls.cfg=json.loads(line);cls.url=cls.cfg["url"];cls.a=cls.cfg["assessment"];cls.b=cls.cfg["otherAssessment"]
    cls.tokens={}
    for role in cls.cfg["users"]:
        status,data=cls.call("/api/login","POST",{"username":role,"password":cls.cfg["users"][role]});assert status==200
        cls.tokens[role]=data["token"]
 @classmethod
 def tearDownClass(cls):
    cls.proc.terminate();cls.proc.communicate(timeout=10)
 @classmethod
 def call(cls,path,method="GET",data=None,token=None,origin=None):
    h={}
    if token:h["Authorization"]="Bearer "+token
    if method=="POST":h.update({"Origin":origin or cls.url,"Content-Type":"application/json"})
    req=urllib.request.Request(cls.url+path,data=json.dumps(data or {}).encode() if method=="POST" else None,headers=h,method=method)
    try:
        with urllib.request.urlopen(req,timeout=5) as r:return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
 def post(self,action,role,data,aid=None):
    return self.call(f"/api/assessments/{aid or self.a}/{action}","POST",data,self.tokens[role])
 def dashboard(self,role,aid=None):return self.call(f"/api/assessments/{aid or self.a}/dashboard",token=self.tokens[role])
 def upload(self,request="SA-01",criterion="Q01",document=None,raw=b"Synthetic evidence only",filename="sample.txt"):
    return self.post("upload","contributor",{"title":"Integrated synthetic mandate","filename":filename,"contentBase64":base64.b64encode(raw).decode(),"documentId":document,"intake":{"criterion":criterion,"requestId":request,"sourceOwner":"Synthetic sponsor","period":"FY26","sourceVersion":"1","locator":"line 1"}})
 def test01_auth_and_assessment_isolation(self):
    self.assertEqual(self.call("/api/assessments")[0],403)
    self.assertEqual(self.dashboard("other")[0],403)
    self.assertEqual(self.dashboard("contributor",self.b)[0],403)
    st,d=self.dashboard("contributor");self.assertEqual(st,200);self.assertEqual(d["catalogue"]["catalogueCount"],32)
    self.assertEqual(len(d["catalogue"]["criteria"]),28)
    self.assertEqual(sum(len(r["criteria"]) for r in d["catalogue"]["requests"]),89)
 def test02_origin_and_role_gates(self):
    self.assertEqual(self.call("/api/login","POST",{"username":"assessor","password":"not a password"},origin="https://unrelated.example")[0],403)
    self.assertEqual(self.post("request","contributor",{"requestId":"SA-01","status":"requested","reason":"Synthetic"})[0],403)
    self.assertEqual(self.upload("LC-01")[0],400)
 def test03_full_workflow(self):
    self.assertEqual(self.post("request","assessor",{"requestId":"SA-01","status":"requested","reason":"Synthetic request"})[0],200)
    st,resp=self.upload();self.assertEqual(st,201);vid=resp["record"]["versionId"]
    self.assertEqual(self.post("preview","reviewer",{"versionId":vid})[0],403)
    self.assertEqual(self.post("inspect","contributor",{"versionId":vid})[0],403)
    self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Not inspected"})[0],400)
    self.assertEqual(self.post("inspect","assessor",{"versionId":vid})[1]["text"],"Synthetic evidence only")
    self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic manual review"})[0],200)
    status,d=self.dashboard("assessor");self.assertEqual(next(r for r in d["catalogue"]["requests"] if r["id"]=="SA-01")["status"],"received")
    self.assertEqual(self.post("preview","reviewer",{"versionId":vid})[1]["text"],"Synthetic evidence only")
    body={"criterion":"Q01","claim":"Synthetic finding","evidenceClass":"E1","strength":"Strong","contradiction":False,"links":[{"versionId":vid,"requestId":"SA-02","locator":"line 1"}]}
    self.assertEqual(self.post("finding","assessor",body)[0],400)
    body["links"][0]["requestId"]="SA-01";st,d=self.post("finding","assessor",body);self.assertEqual(st,201);fid=d["findingId"]
    review={"findingId":fid,"decision":"accept","reason":"Synthetic independent assessment","confirmed":True}
    self.assertEqual(self.post("review","assessor",review)[0],403)
    self.assertEqual(self.post("review","reviewer",review)[0],200)
    self.assertEqual(self.dashboard("owner")[1]["findings"][0]["state"],"accept")
    self.assertEqual(self.dashboard("contributor")[1]["findings"],[])
    self.assertEqual(self.post("release","owner",{})[0],403)
    st,d=self.upload(document=resp["record"]["documentId"]);self.assertEqual(st,201);self.assertEqual(d["record"]["version"],2)
    self.assertEqual(self.dashboard("owner")[1]["findings"][0]["state"],"superseded")
 def test04_logout_revokes_token(self):
    st,r=self.call("/api/login","POST",{"username":"reviewer","password":self.cfg["users"]["reviewer"]});self.assertEqual(st,200)
    self.assertEqual(self.call("/api/logout","POST",{},r["token"])[0],200)
    self.assertEqual(self.call("/api/assessments",token=r["token"])[0],403)
 def test05_extraction_review_and_provenance(self):
    fixture=json.loads((HERE/"golden-fixtures.json").read_text())["fixtures"][0]
    st,d=self.upload(raw=fixture["text"].encode());self.assertEqual(st,201);v=d["record"];vid=v["versionId"]
    self.assertEqual(self.post("extract","assessor",{"versionId":vid,"criterion":"Q01"})[0],400)
    self.post("inspect","assessor",{"versionId":vid});self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic"})[0],200)
    self.assertEqual(self.post("extract","assessor",{"versionId":vid,"criterion":"Q10"})[0],400)
    self.assertEqual(self.post("extract","contributor",{"versionId":vid,"criterion":"Q01"})[0],403)
    self.assertEqual(self.post("extract","assessor",{"versionId":vid,"criterion":"Q01","mode":"narrative"})[0],400)
    st,d=self.post("extract","assessor",{"versionId":vid,"criterion":"Q01"});self.assertEqual(st,201);rid=d["runId"]
    records=self.dashboard("reviewer")[1]["extractions"];r=next(x for x in records if x["id"]==rid);self.assertEqual(r["sourceSha256"],v["sha256"]);self.assertEqual(r["result"]["counts"]["present"],5);self.assertEqual(r["result"]["fields"][0]["citations"][0]["location"],"Text line 3")
    self.assertEqual(self.dashboard("contributor")[1]["extractions"],[])
    review={"runId":rid,"decision":"accept","reason":"Reviewed exact citations","confirmed":True}
    self.assertEqual(self.post("extraction-review","assessor",review)[0],403)
    self.assertEqual(self.post("extraction-review","reviewer",review)[0],400)
    self.post("preview","reviewer",{"versionId":vid});self.assertEqual(self.post("extraction-review","reviewer",review)[0],200)
    self.assertEqual(next(x for x in self.dashboard("owner")[1]["extractions"] if x["id"]==rid)["state"],"accept")
    self.assertEqual(self.post("extraction-review","reviewer",review)[0],400)
    self.assertEqual(self.upload(document=v["documentId"],raw=b"Synthetic replacement")[0],201)
    self.assertEqual(next(x for x in self.dashboard("owner")[1]["extractions"] if x["id"]==rid)["state"],"superseded")
 def test06_missing_fields_return_not_accept(self):
    st,d=self.upload(raw=b"Unstructured synthetic text only");self.assertEqual(st,201);vid=d["record"]["versionId"]
    self.post("inspect","assessor",{"versionId":vid});self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic"})
    st,d=self.post("extract","assessor",{"versionId":vid,"criterion":"Q01"});self.assertEqual(st,201);rid=d["runId"]
    self.post("preview","reviewer",{"versionId":vid})
    self.assertEqual(self.post("extraction-review","reviewer",{"runId":rid,"decision":"accept","reason":"Synthetic","confirmed":True})[0],400)
    self.assertEqual(self.post("extraction-review","reviewer",{"runId":rid,"decision":"return","reason":"Missing fields"})[0],200)
 def test07_supported_document_formats_end_to_end(self):
    import zipfile
    for ext in ["pdf","docx","xlsx"]:
        with zipfile.ZipFile(HERE/"document-fixtures.zip") as z:raw=z.read("Q01."+ext)
        st,d=self.upload(raw=raw,filename="Q01."+ext);self.assertEqual(st,201);vid=d["record"]["versionId"]
        st,preview=self.post("inspect","assessor",{"versionId":vid});self.assertEqual(st,200);self.assertIn("Reduce fictional processing delay",preview["text"])
        self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic document inspected"})[0],200)
        st,r=self.post("extract","assessor",{"versionId":vid,"criterion":"Q01"});self.assertEqual(st,201)
        ex=next(x for x in self.dashboard("reviewer")[1]["extractions"] if x["id"]==r["runId"])
        self.assertEqual(ex["result"]["format"],ext);self.assertEqual(ex["result"]["counts"]["present"],5)
        self.assertEqual(self.post("preview","reviewer",{"versionId":vid})[0],200)
        self.assertEqual(self.post("extraction-review","reviewer",{"runId":r["runId"],"decision":"accept","reason":"Synthetic precise location review","confirmed":True})[0],200)
 def test08_interview_api_role_isolation_and_followups(self):
    st,d=self.post("interview-start","assessor",{"persona":"Synthetic sponsor","stakeholderRef":"SYN-P1","role":"Sponsor","scope":"Synthetic interview"});self.assertEqual(st,201);one=d["sessionId"]
    st,d=self.post("interview-start","assessor",{"persona":"Synthetic finance lead","stakeholderRef":"SYN-P2","role":"Finance","scope":"Synthetic interview"});self.assertEqual(st,201);two=d["sessionId"]
    self.assertEqual(self.post("interview-start","reviewer",{"persona":"Synthetic","stakeholderRef":"x","role":"Reviewer","scope":"Synthetic"})[0],403)
    body={"sessionId":one,"questionId":"Q26","status":"answered","verbatim":"Forecast SGD 9000","interpretation":"Forecast not an actual","flags":["forecast_vs_actual"],"links":[]}
    st,d=self.post("interview-response","assessor",body);self.assertEqual(st,201);a=d["claimId"]
    st,d=self.post("interview-response","assessor",{**body,"sessionId":two,"verbatim":"No validated actual outcome"});self.assertEqual(st,201);b=d["claimId"]
    self.assertEqual(self.post("interview-conflict","assessor",{"claimA":a,"claimB":b,"topic":"Forecast vs actual","material":True})[0],201)
    view=self.dashboard("assessor")[1]["interviews"];self.assertEqual(len(view["questions"]),28);self.assertEqual(len(view["claims"]),2)
    claim=next(c for c in view["claims"] if c["id"]==a);self.assertEqual(claim["suggestion"]["triggerId"],"FUP-04");self.assertFalse(claim["scoringEligible"])
    st,d=self.post("interview-followup","assessor",{"claimId":a,"triggerId":"FUP-04","question":claim["suggestion"]["question"]});self.assertEqual(st,201);f=d["followUpId"]
    self.assertEqual(self.post("interview-followup","assessor",{"claimId":a,"triggerId":"FUP-04","question":"Second"} )[0],400)
    self.assertEqual(self.post("interview-answer","assessor",{"followUpId":f,"status":"answered","verbatim":"Actual evidence remains missing"})[0],200)
    self.assertEqual(self.post("interview-review","assessor",{"claimId":a,"decision":"confirm_capture","reason":"Synthetic","confirmed":True})[0],403)
    self.assertEqual(self.post("interview-review","reviewer",{"claimId":a,"decision":"confirm_capture","reason":"Capture only","confirmed":True})[0],200)
    owner=next(c for c in self.dashboard("owner")[1]["interviews"]["claims"] if c["id"]==a);self.assertEqual(owner["captureReview"]["decision"],"confirm_capture");self.assertEqual(owner["validationStatus"],"unverified interview claim")
    self.assertIsNone(self.dashboard("contributor")[1]["interviews"]);self.assertEqual(self.dashboard("other")[0],403);self.assertEqual(self.post("release","owner",{})[0],403)
 def test09_validation_integration(self):
    # Q02 avoids the material Q01 contradiction recorded in the interview regression.
    rule=next(x for x in self.dashboard("owner")[1]["validation"]["rules"] if x["criterionId"]=="Q02")
    st,r=self.upload(rule["primary"][0],"Q02",raw=b"Fictional second criterion source")
    self.assertEqual(st,201);vid=r["record"]["versionId"]
    self.assertEqual(self.post("inspect","assessor",{"versionId":vid})[0],200)
    self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic"})[0],200)
    v=next(x for x in self.dashboard("assessor")[1]["versions"] if x["versionId"]==vid)
    body=dict(criterion="Q02",applicability="applicable",condition="met",evidenceClass="E1",strength="Strong",fieldsVerified=True,comparable=True,materialityReviewed=True,requiresCorroboration=False,documentaryConflict=False,claim="Synthetic condition",rationale="Synthetic rationale",owner="Fictional owner",conditionalApplies=None,refs=[dict(versionId=vid,requestId=v["requestId"],locator="Text line 1",quote="Fictional second criterion source")],claimIds=[])
    self.assertEqual(self.post("validation-draft","contributor",body)[0],403)
    st,r=self.post("validation-draft","assessor",body);self.assertEqual(st,201);did=r["draftId"]
    review=dict(draftId=did,decision="accept",reason="Synthetic independent review",controls={"confirmed":True})
    self.assertEqual(self.post("validation-review","reviewer",review)[0],400)
    self.assertEqual(self.post("preview","reviewer",{"versionId":vid})[0],200)
    self.assertEqual(self.post("validation-review","reviewer",review)[0],201)
    result=next(x for x in self.dashboard("owner")[1]["validation"]["drafts"] if x["id"]==did)
    self.assertEqual(result["state"]["state"],"supported_met");self.assertFalse(result["scoringEligible"])
    self.assertIsNone(self.dashboard("contributor")[1]["validation"])
 def test10_pilot_scoring_disabled_by_default(self):
    self.assertEqual(self.dashboard("owner")[1]["pilotScoring"],{"enabled":False,"finalScoringLocked":True})
    self.assertIsNone(self.dashboard("contributor")[1]["pilotScoring"])
    body={"criterion":"Q01","validationId":"synthetic","score":3,"rationale":"Synthetic","operating":False,"redFlag":""}
    self.assertEqual(self.post("pilot-score-draft","assessor",body)[0],403)
    self.assertEqual(self.post("release","owner",{})[0],403)
 def test11_executive_decision_workflow(self):
    st,d=self.dashboard("owner");self.assertEqual(st,200)
    snap=d["executive"]["snapshot"];self.assertEqual(len(snap["criteria"]),28)
    ids=[c["validationId"] for c in snap["criteria"] if c["state"] in ("supported_met","supported_not_met")]
    body={"title":"Synthetic executive brief","summary":"Fictional synthesis","limitations":"Incomplete fictional coverage","findingIds":ids,"options":[{"direction":"Correct","rationale":"Synthetic","consequences":"Synthetic"},{"direction":"Reassess","rationale":"Synthetic","consequences":"Synthetic"}],"actions":[{"condition":"Synthetic gap","owner":"Fictional sponsor","followUp":"Gather synthetic evidence"}]}
    self.assertEqual(self.post("executive-draft","contributor",body)[0],403)
    st,r=self.post("executive-draft","assessor",body);self.assertEqual(st,201);bid=r["briefId"]
    direction={"briefId":bid,"direction":"Reassess","reason":"Fictional owner rationale","conditions":"Synthetic open gaps","confirmed":True}
    self.assertEqual(self.post("executive-direction","owner",direction)[0],400)
    review={"briefId":bid,"decision":"accept","reason":"Synthetic review","confirmed":True}
    self.assertEqual(self.post("executive-review","assessor",review)[0],403)
    for c in snap["criteria"]:
      if c["state"] in ("supported_met","supported_not_met"):
        for ref in c["refs"]:self.assertEqual(self.post("preview","reviewer",{"versionId":ref["versionId"]})[0],200)
    self.assertEqual(self.post("executive-review","reviewer",review)[0],201)
    self.assertEqual(self.post("executive-direction","owner",dict(direction,direction="Correct"))[0],400)
    self.assertEqual(self.post("executive-direction","owner",direction)[0],201)
    b=next(b for b in self.dashboard("owner")[1]["executive"]["briefs"] if b["id"]==bid)
    self.assertEqual(b["state"],"reviewed_with_gaps");self.assertTrue(b["directionCurrent"])
    self.assertIsNone(self.dashboard("contributor")[1]["executive"]);self.assertEqual(self.post("release","owner",{})[0],403)
 def test12_reassessment_workflow(self):
    ids=[]
    for title,start,end in [("Baseline","2026-01-01","2026-03-31"),("Follow-up","2026-04-01","2026-06-30")]:
      body={"label":title,"periodStart":start,"periodEnd":end,"basis":"Synthetic consistent population"}
      self.assertEqual(self.post("reassessment-capture","contributor",body)[0],403)
      st,r=self.post("reassessment-capture","assessor",body);self.assertEqual(st,201);sid=r["snapshotId"];ids.append(sid)
      self.assertEqual(self.post("reassessment-snapshot-review","reviewer",{"snapshotId":sid,"decision":"accept","reason":"Synthetic","confirmed":True})[0],201)
    snap=self.dashboard("owner")[1]["reassessment"]["snapshots"][0]
    actions=[{"actionId":a["id"],"status":"open","rationale":"Still open","findingIds":[]} for a in (snap["payload"]["state"]["executive"] or {}).get("actions",[])]
    body={"baselineId":ids[0],"followUpId":ids[1],"rationale":"Synthetic comparison","confirmed":True,"actions":actions}
    st,r=self.post("reassessment-compare","assessor",body);self.assertEqual(st,201);cid=r["comparisonId"]
    self.assertEqual(self.post("reassessment-comparison-review","owner",{"comparisonId":cid,"decision":"accept","reason":"Synthetic","confirmed":True})[0],403)
    self.assertEqual(self.post("reassessment-comparison-review","reviewer",{"comparisonId":cid,"decision":"accept","reason":"Synthetic","confirmed":True})[0],201)
    c=self.dashboard("owner")[1]["reassessment"]["comparisons"][0]
    self.assertEqual(c["status"],"accept");self.assertEqual(len(c["payload"]["result"]["dimensions"]),7);self.assertIsNone(c["payload"]["result"]["pilot"])
    self.assertIsNone(self.dashboard("contributor")[1]["reassessment"]);self.assertEqual(self.post("release","owner",{})[0],403)
 def test13_evidence_matching_human_link(self):
    st,r=self.upload("PC-04","Q13",raw=b"Weekly active users: 70% adoption.");self.assertEqual(st,201);vid=r["record"]["versionId"]
    self.assertEqual(self.post("inspect","assessor",{"versionId":vid})[0],200)
    self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic"})[0],200)
    body={"criterion":"Q13","query":"Weekly active users: 80% adoption","mode":"ranked"}
    self.assertEqual(self.post("matching-propose","contributor",body)[0],403)
    st,r=self.post("matching-propose","assessor",body);self.assertEqual(st,201);rid=r["runId"]
    result=next(x for x in self.dashboard("owner")[1]["matching"]["runs"] if x["id"]==rid)
    c=next(c for c in result["candidates"] if c["versionId"]==vid);self.assertIn("possible_numeric_difference_check_basis",c["hints"])
    review={"runId":rid,"candidateId":c["id"],"decision":"link","reason":"Synthetic relevance review","confirmed":True}
    self.assertEqual(self.post("matching-review","assessor",review)[0],400)
    self.assertEqual(self.post("preview","assessor",{"versionId":vid})[0],200)
    self.assertEqual(self.post("matching-review","assessor",review)[0],201)
    d=dict(criterion="Q13",applicability="applicable",condition="not_met",evidenceClass="E1",strength="Strong",fieldsVerified=True,comparable=True,materialityReviewed=True,requiresCorroboration=False,documentaryConflict=False,claim="Synthetic adverse condition",rationale="Synthetic rationale",owner="Fictional owner",conditionalApplies=None,refs=[],claimIds=[],matchIds=[c["id"]])
    st,r=self.post("validation-draft","assessor",d);self.assertEqual(st,201);did=r["draftId"]
    finding=next(x for x in self.dashboard("owner")[1]["validation"]["drafts"] if x["id"]==did);self.assertEqual(finding["state"]["state"],"review_pending");self.assertEqual(finding["payload"]["refs"][0]["quote"],c["quote"])
    self.assertIsNone(self.dashboard("contributor")[1]["matching"])
if __name__=="__main__":unittest.main(verbosity=2)
