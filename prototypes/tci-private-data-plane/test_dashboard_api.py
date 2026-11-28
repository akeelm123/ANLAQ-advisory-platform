"""Isolated synthetic HTTP and recovery tests for the dashboard UAT."""
import base64,json,secrets,tempfile,threading,unittest,urllib.error,urllib.request
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch
from local_store import LocalStore,ROLES
from dashboard_persistent import DashboardWorkspaceStore,make_server
from serve import REGISTER,SPEC
class DashboardAPITests(unittest.TestCase):
    def request(self,server,path,data=None,token=None,origin=True):
        url=f"http://127.0.0.1:{server.server_port}"
        h={"Content-Type":"application/json"}
        if token:h["Authorization"]="Bearer "+token
        if origin:h["Origin"]=url
        req=urllib.request.Request(url+path,data=None if data is None else json.dumps(data).encode(),headers=h)
        def client():
            try:
                with urllib.request.urlopen(req,timeout=20) as r:return r.status,json.load(r)
            except urllib.error.HTTPError as e:return e.code,json.load(e)
        with ThreadPoolExecutor(1) as pool:
            future=pool.submit(client);server.handle_request();return future.result(timeout=20)
    def run_server(self,workspace):
        server=make_server(workspace,0);server.timeout=20;self.addCleanup(server.server_close);return server
    def test_persistent_routes_role_scope_and_checkpoint_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"vault";passphrase=secrets.token_urlsafe(24);accounts={r:(r+"-named",secrets.token_urlsafe(20)) for r in ROLES}
            with LocalStore(root,REGISTER,SPEC) as store:
                aid=store.initialize(passphrase,accounts,"Fictional dashboard UAT")
                w=DashboardWorkspaceStore(store,aid,initialize=True)
                server=self.run_server(w)
                def sign(role):
                    u,p=accounts[role];return self.request(server,"/api/login",{"username":u,"password":p})[1]["token"]
                assessor=sign("assessor");contributor=sign("contributor")
                self.assertEqual(self.request(server,"/api/workspace",token=contributor)[0],403)
                self.assertEqual(self.request(server,"/api/workspace",token=None)[0],403)
                upload={"filename":"mock.txt","content":base64.b64encode(b"Fictional strategy objectives and original business problem.").decode(),"synthetic":True,"requestId":"SA-01"}
                self.assertEqual(self.request(server,"/api/upload",upload,assessor,origin=False)[0],403)
                self.assertEqual(self.request(server,"/api/upload",{**upload,"synthetic":False},assessor)[0],400)
                code,doc=self.request(server,"/api/upload",upload,assessor);self.assertEqual(code,201)
                self.assertEqual(self.request(server,"/api/source",{"digest":doc["digest"]},assessor)[1]["digest"],doc["digest"])
                workspace={"answers":{"Q01":"Fictional saved response"},"reviews":{},"edits":{},"title":"Saved fictional assessment","persona":"Board"}
                self.assertEqual(self.request(server,"/api/workspace",workspace,assessor)[0],200)
                self.assertEqual(self.request(server,"/api/snapshot",{},assessor)[0],201)
                archive=store.current.read_bytes()
                self.assertNotIn(b"Fictional saved response",archive)
                with patch.object(store,"checkpoint",side_effect=OSError("mock checkpoint failure")):
                    self.assertEqual(self.request(server,"/api/workspace",{**workspace,"title":"Unacknowledged change"},assessor)[0],503)
                self.assertEqual(self.request(server,"/api/workspace",token=assessor)[0],503)
                self.assertEqual(store.current.read_bytes(),archive)
                server.server_close()
            with LocalStore(root,REGISTER,SPEC) as store:
                store.unlock(passphrase);w=DashboardWorkspaceStore(store,aid)
                self.assertEqual(w.assessment.workspace_view()["title"],workspace["title"])
                self.assertEqual(len(w.assessment.workspace_view()["snapshots"]),1)
                self.assertEqual(w.assessment.source(doc["digest"])["digest"],doc["digest"])
