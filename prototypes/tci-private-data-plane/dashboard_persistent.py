"""Separate encrypted fictional dashboard UAT vault. Never point at an existing workbench vault."""
import argparse,getpass,json,signal
from http.server import HTTPServer
from pathlib import Path
from data_plane import Invalid
from document_parser import enable_child_parser
from local_store import LocalStore,ROLES
from local_pilot import prompt_secret
from serve import REGISTER,SPEC
from simple_preview import SimpleHandler
from dashboard_logic import DashboardAssessment

def new_assessment():
    return DashboardAssessment(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))

class DashboardWorkspaceStore:
    def __init__(self,store,aid,initialize=False):
        self.store=store;self.dp=store.dp;self.aid=aid;self.assessment=new_assessment()
        exists=self.dp.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='dashboard_uat_workspace'").fetchone()
        if initialize:
            if exists:raise Invalid("Dashboard workspace already exists")
            self.dp.db.execute("CREATE TABLE dashboard_uat_workspace(assessment_id TEXT PRIMARY KEY REFERENCES assessments(id),payload TEXT NOT NULL)")
            self.dp.db.execute("INSERT INTO dashboard_uat_workspace VALUES (?,?)",(aid,self.dp.validation._seal(self.key,self.assessment.export_state())))
            self.dp.db.commit();store.checkpoint()
        else:
            if not exists:raise Invalid("Not a dashboard UAT vault. Do not use existing workbench vault.")
            row=self.dp.db.execute("SELECT payload FROM dashboard_uat_workspace WHERE assessment_id=?",(aid,)).fetchone()
            if not row:raise Invalid("Dashboard workspace not found")
            self.assessment.restore_state(self.dp.validation._open(self.key,row["payload"]))
    @property
    def key(self):return "dashboard-uat-"+self.aid
    def checkpoint(self,actor):
        state=self.assessment.export_state()
        with self.dp.db:
            self.dp.db.execute("UPDATE dashboard_uat_workspace SET payload=? WHERE assessment_id=?",(self.dp.validation._seal(self.key,state),self.aid))
            self.dp._audit(self.aid,actor,"fictional dashboard workspace checkpoint",self.aid)
        self.store.checkpoint()

class PersistentDashboardHandler(SimpleHandler):
    def execute(self,method):
        if self.server.failed:return super().payload(503,{"error":"Checkpoint failed; stop and restart from last durable archive"})
        return super().execute(method)
    def payload(self,status,data):
        if self.command=="POST" and 200<=status<300 and self.path in ("/api/upload","/api/propose","/api/workspace","/api/snapshot","/api/example"):
            try:
                actor=self.dp._actor(self.token(),self.server.aid,{"assessor"})
                self.server.workspace_store.checkpoint(actor["id"])
            except Exception:
                self.server.failed=True;return super().payload(503,{"error":"Encrypted checkpoint failed; progress was not acknowledged. Restart and inspect the previous archive."})
        return super().payload(status,data)

def make_server(workspace,port,model=False):
    enable_child_parser()
    server=HTTPServer(("127.0.0.1",port),PersistentDashboardHandler)
    server.dp=workspace.dp;server.aid=workspace.aid;server.dashboard=True;server.model_enabled=model;server.assessment=workspace.assessment;server.workspace_store=workspace;server.failed=False
    return server
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--data-dir",default=str(Path.home()/"Library/Application Support/ANLAQ-TCI-Dashboard-UAT"));p.add_argument("--port",type=int,default=8775);p.add_argument("--initialize",action="store_true");p.add_argument("--confirm-synthetic",action="store_true");p.add_argument("--enable-local-model",action="store_true");a=p.parse_args()
    if not a.confirm_synthetic:p.error("Explicit fictional-only confirmation required")
    with LocalStore(a.data_dir,REGISTER,SPEC) as store:
        if a.initialize:
            if store.current.exists() or store.saltfile.exists():p.error("Select a NEW empty dashboard vault")
            password=prompt_secret("New dashboard vault passphrase",16);accounts={r:(input(r.capitalize()+" username: ").strip(),prompt_secret(r+" password",16)) for r in ROLES};aid=store.initialize(password,accounts,title="Fictional dashboard UAT")
            w=DashboardWorkspaceStore(store,aid,initialize=True)
        else:
            store.unlock(getpass.getpass("Dashboard UAT vault passphrase: "))
            rows=store.dp.db.execute("SELECT id FROM assessments").fetchall()
            if len(rows)!=1:raise Invalid("Select dedicated dashboard UAT vault")
            w=DashboardWorkspaceStore(store,rows[0]["id"])
        signal.signal(signal.SIGTERM,lambda *_:exit(0))
        with make_server(w,a.port,a.enable_local_model) as server:
            print(json.dumps({"url":f"http://127.0.0.1:{server.server_port}","scope":"fictional encrypted UAT only"}),flush=True)
            try:server.serve_forever()
            except KeyboardInterrupt:pass
if __name__=="__main__":main()
