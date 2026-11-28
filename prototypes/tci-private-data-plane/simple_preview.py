"""Separate authenticated, fictional, memory-only simplified UX. Never production."""
import argparse,base64,binascii,json,secrets,signal,webbrowser,errno
from http.server import HTTPServer
from serve import Handler,HERE,REGISTER,SPEC,Denied,Invalid
from validation_demo import DataPlaneContext
from document_parser import enable_child_parser
from simple_scoring import SimpleAssessment
from simple_ai import propose
from dashboard_logic import DashboardAssessment

STATIC={"/":("simple.html","text/html; charset=utf-8"),"/simple.js":("simple.js","text/javascript; charset=utf-8"),"/simple.css":("simple.css","text/css; charset=utf-8"),"/logo.svg":("logo.svg","image/svg+xml")}
DASHBOARD_STATIC={"/":("dashboard.html","text/html; charset=utf-8"),"/dashboard.js":("dashboard.js","text/javascript; charset=utf-8"),"/dashboard.css":("dashboard.css","text/css; charset=utf-8"),"/logo.svg":("logo.svg","image/svg+xml")}
class SimpleHandler(Handler):
    def execute(self,method):
        if not self.host_ok():return self.payload(403,{"error":"Access denied"})
        try:
            static=DASHBOARD_STATIC if self.server.dashboard else STATIC
            if method=="GET" and self.path in static:
                fname,ctype=static[self.path];data=(HERE/fname).read_bytes();self.headers_for(200,ctype,len(data));self.wfile.write(data);return
            if method=="POST":
                if self.headers.get("Origin")!=self.origin:raise Denied("Origin denied")
                data=self.body()
            else:data={}
            if self.path=="/api/login" and method=="POST":
                token=self.dp.login(data["username"],data["password"]);return self.payload(200,{"token":token})
            try:
                token=self.token();self.dp._session_user(token)
            except Denied:return self.payload(401,{"error":"Your session has expired. Sign in again.","code":"SESSION_EXPIRED"})
            actor=self.dp._actor(token,self.server.aid,{"assessor"});self.request_actor_id=actor["id"]
            assessment=self.server.assessment
            if method=="GET" and self.path=="/api/methodology":return self.payload(200,{**assessment.metadata(),"modelEnabled":self.server.model_enabled})
            if method=="GET" and self.path=="/api/analyze":return self.payload(200,assessment.analyze())
            if self.server.dashboard and self.path=="/api/workspace":
                if method=="GET":return self.payload(200,assessment.workspace_view())
                if method=="POST":return self.payload(200,assessment.save_workspace(data))
            if self.server.dashboard and method=="POST" and self.path=="/api/snapshot":return self.payload(201,assessment.snapshot())
            if self.server.dashboard and method=="POST" and self.path=="/api/snapshot-detail":return self.payload(200,assessment.snapshot_detail(data["id"]))
            if self.server.dashboard and method=="POST" and self.path=="/api/example":
                if data.get("synthetic") is not True:raise Invalid("Confirm fictional example")
                return self.payload(201,assessment.load_example(json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"]))
            if self.server.dashboard and method=="POST" and self.path=="/api/source":return self.payload(200,assessment.source(data["digest"]))
            if method=="POST" and self.path=="/api/upload":
                if data.get("synthetic") is not True:raise Invalid("Confirm fictional input")
                args=(data["filename"],base64.b64decode(data["content"],validate=True))
                return self.payload(201,assessment.add(*args,request_id=data.get("requestId")) if self.server.dashboard else assessment.add(*args))
            if method=="POST" and self.path=="/api/propose":
                if not self.server.model_enabled:raise Denied("Model disabled")
                result=propose(assessment,data["dimension"],data["interviews"]);assessment.record_proposals(result["candidates"],data["interviews"],result.get("model"),result.get("modelDigest"));return self.payload(200,result)
            if method=="POST" and self.path=="/api/calculate":return self.payload(200,assessment.calculate(data["rows"],data["interviews"]))
            if method=="POST" and self.path=="/api/logout":
                self.dp.logout(token);return self.payload(200,{"ok":True})
            return self.payload(404,{"error":"Unknown route"})
        except Denied:return self.payload(403,{"error":"Access denied"})
        except (Invalid,ValueError,TypeError,KeyError,binascii.Error) as e:return self.payload(400,{"error":str(e)[:200]})
        except Exception:return self.payload(500,{"error":"Preview request failed"})

def main():
    p=argparse.ArgumentParser();p.add_argument("--port",type=int,default=8770);p.add_argument("--enable-local-model",action="store_true");p.add_argument("--dashboard",action="store_true");p.add_argument("--open-browser",action="store_true");p.add_argument("--auto-port",action="store_true");a=p.parse_args()
    enable_child_parser()
    with DataPlaneContext() as dp:
        aid=dp.bootstrap_assessment("Fictional simplified preview","Fictional assessment","Temporary demo only")
        password=secrets.token_urlsafe(20);uid=dp.bootstrap_user("assessor",password);dp.bootstrap_membership(aid,uid,"assessor")
        try:server=HTTPServer(("127.0.0.1",a.port),SimpleHandler)
        except OSError as e:
            if not a.auto_port or e.errno!=errno.EADDRINUSE:raise
            server=HTTPServer(("127.0.0.1",0),SimpleHandler)
        with server:
            server.dp=dp;server.aid=aid;server.model_enabled=a.enable_local_model;server.dashboard=a.dashboard;server.assessment=(DashboardAssessment if a.dashboard else SimpleAssessment)(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))
            print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}","username":"assessor","password":password}),flush=True)
            if a.open_browser:webbrowser.open(f"http://127.0.0.1:{server.server_port}/")
            signal.signal(signal.SIGTERM,lambda *_:exit(0))
            try:server.serve_forever()
            except KeyboardInterrupt:pass
if __name__=="__main__":main()
