"""Loopback synthetic persistence API and fail-closed checkpoint tests."""
import base64,json,secrets,subprocess,sys,tempfile,unittest,urllib.request,urllib.error
from pathlib import Path
from local_store import ROLES
HERE=Path(__file__).resolve().parent

class LocalAPITests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.cfg={"directory":str(Path(self.tmp.name)/"vault"),"passphrase":secrets.token_urlsafe(24),"accounts":{r:[r+"-named",secrets.token_urlsafe(24)] for r in ROLES},"initialize":True};self.proc=None
 def tearDown(self):self.stop();self.tmp.cleanup()
 def start(self,initialize=False,fail=False):
    self.stop();self.proc=subprocess.Popen([sys.executable,str(HERE/"local_test_server.py")],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    self.proc.stdin.write(json.dumps(self.cfg|{"initialize":initialize,"simulateCheckpointFailure":fail})+"\n");self.proc.stdin.close()
    line=self.proc.stdout.readline()
    if not line:raise RuntimeError("Synthetic local server failed to start")
    cfg=json.loads(line);self.url=cfg["url"];self.a=cfg["assessment"];self.tokens={}
    for r in ROLES:
      name,pw=self.cfg["accounts"][r];st,d=self.call("/api/login","POST",{"username":name,"password":pw});self.assertEqual(st,200);self.tokens[r]=d["token"]
 def stop(self):
    if self.proc:
      self.proc.terminate();self.proc.wait(timeout=10);self.proc.stdout.close();self.proc.stderr.close();self.proc=None
 def call(self,path,method="GET",data=None,token=None):
    headers={}
    if token:headers["Authorization"]="Bearer "+token
    if method=="POST":headers.update({"Origin":self.url,"Content-Type":"application/json"})
    req=urllib.request.Request(self.url+path,data=json.dumps(data or {}).encode() if method=="POST" else None,headers=headers,method=method)
    try:
      with urllib.request.urlopen(req,timeout=10) as r:return r.status,json.loads(r.read())
    except urllib.error.HTTPError as e:return e.code,json.loads(e.read())
 def post(self,action,role,body):return self.call(f"/api/assessments/{self.a}/{action}","POST",body,self.tokens[role])
 def dash(self,role):return self.call(f"/api/assessments/{self.a}/dashboard",token=self.tokens[role])
 def upload(self):return self.post("upload","contributor",{"title":"Fictional persisted source","filename":"source.txt","contentBase64":base64.b64encode(b"Synthetic persistent source").decode(),"intake":{"criterion":"Q01","requestId":"SA-01","sourceOwner":"Fictional owner","period":"Test","sourceVersion":"1","locator":"Text line 1"}})
 def test_restart_and_role_revocation(self):
    self.start(True);old=self.tokens["owner"];st,r=self.upload();self.assertEqual(st,201);vid=r["record"]["versionId"]
    self.start();self.assertEqual(self.call("/api/assessments",token=old)[0],403)
    self.assertTrue(self.dash("owner")[1]["localPersistent"]);self.assertEqual(self.dash("owner")[1]["versions"][0]["versionId"],vid)
    self.assertEqual(self.post("inspect","assessor",{"versionId":vid})[0],200);self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic"})[0],200)
    member=next(x for x in self.dash("owner")[1]["localMembers"] if x["role"]=="contributor")
    self.assertEqual(self.dash("reviewer")[1]["localMembers"],[])
    self.assertEqual(self.post("local-revoke-membership","assessor",{"userId":member["id"],"confirmed":True})[0],403)
    self.assertEqual(self.post("local-revoke-membership","owner",{"userId":member["id"],"confirmed":False})[0],400)
    self.assertEqual(self.post("local-revoke-membership","owner",{"userId":member["id"],"confirmed":True})[0],200)
    self.assertEqual(self.dash("contributor")[0],403)
    self.start();self.assertEqual(self.dash("contributor")[0],403);self.assertEqual(self.post("preview","reviewer",{"versionId":vid})[1]["text"],"Synthetic persistent source");self.assertEqual(self.post("release","owner",{})[0],403)
 def test_checkpoint_failure_not_acknowledged(self):
    self.start(True);self.start(fail=True)
    self.assertEqual(self.upload()[0],503);self.assertEqual(self.dash("owner")[0],503)
    self.start();self.assertEqual(self.dash("owner")[1]["versions"],[])
 def test_port_collision_uses_free_loopback_port(self):
    from http.server import HTTPServer,BaseHTTPRequestHandler
    from local_store import LocalStore
    from local_pilot import make_server
    from serve import REGISTER,SPEC
    with HTTPServer(("127.0.0.1",0),BaseHTTPRequestHandler) as occupied:
      with LocalStore(self.cfg["directory"],REGISTER,SPEC) as s:
        s.initialize(self.cfg["passphrase"],self.cfg["accounts"])
        with self.assertRaises(OSError):make_server(s,occupied.server_port)
        with make_server(s,occupied.server_port,auto_port=True) as server:
          self.assertNotEqual(server.server_port,occupied.server_port)
          self.assertEqual(server.server_address[0],"127.0.0.1")
 def test_strict_intake_refusal_persists_without_document(self):
    self.cfg["requireScan"]=True;self.cfg["mockScannerStatus"]="unavailable"
    self.start(True);self.assertEqual(self.upload()[0],400)
    d=self.dash("owner")[1];self.assertEqual(d["versions"],[]);self.assertEqual(d["intakeAssurance"]["policy"],"require_clean_scan");self.assertEqual(d["intakeAssurance"]["records"][0]["scanStatus"],"unavailable")
    self.start();d=self.dash("owner")[1];self.assertEqual(d["versions"],[]);self.assertEqual(d["intakeAssurance"]["records"][0]["outcome"],"refused")
    self.assertIsNone(self.dash("contributor")[1]["intakeAssurance"])
if __name__=="__main__":unittest.main()
