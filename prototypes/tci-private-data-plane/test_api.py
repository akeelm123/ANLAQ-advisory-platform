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
if __name__=="__main__":unittest.main(verbosity=2)
