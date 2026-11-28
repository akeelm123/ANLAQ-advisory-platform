"""Synthetic-only browser regression harness; controlled clock input over stdin, no test HTTP route."""
import json,secrets,sys,threading,time
from http.server import HTTPServer
from simple_preview import SimpleHandler,REGISTER,SPEC
from validation_demo import DataPlaneContext
from dashboard_logic import DashboardAssessment
class LegacyHandler(SimpleHandler):
    def payload(self,status,data):
        return super().payload(403,{"error":"Access denied"}) if status==401 else super().payload(status,data)
def main():
    with DataPlaneContext() as dp:
        offset=[0];dp.clock=lambda:time.time()+offset[0]
        aid=dp.bootstrap_assessment("Fictional session test","Fictional session test","Test only")
        password=secrets.token_urlsafe(24);uid=dp.bootstrap_user("assessor",password);dp.bootstrap_membership(aid,uid,"assessor")
        with HTTPServer(("127.0.0.1",0),LegacyHandler if "--legacy" in sys.argv else SimpleHandler) as server:
            server.dp=dp;server.aid=aid;server.dashboard=True;server.model_enabled=False;server.assessment=DashboardAssessment(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))
            print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}","username":"assessor","password":password}),flush=True)
            def control():
                for line in sys.stdin:
                    if line.strip()=="EXPIRE":offset[0]+=1801;print("EXPIRED",flush=True)
            threading.Thread(target=control,daemon=True).start();server.serve_forever()
if __name__=="__main__":main()
