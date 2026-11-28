import json,secrets,tempfile,unittest
from pathlib import Path
from local_store import LocalStore,ROLES
from dashboard_persistent import DashboardWorkspaceStore
from serve import REGISTER,SPEC
class DashboardPersistenceTests(unittest.TestCase):
    def test_encrypted_checkpoint_and_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)/"vault";passphrase=secrets.token_urlsafe(24);accounts={r:(r+"-named",secrets.token_urlsafe(20)) for r in ROLES}
            with LocalStore(root,REGISTER,SPEC) as store:
                aid=store.initialize(passphrase,accounts,title="Fictional dashboard UAT")
                w=DashboardWorkspaceStore(store,aid,initialize=True)
                token=store.dp.login(*accounts["assessor"]);actor=store.dp._actor(token,aid,{"assessor"})["id"]
                f=w.assessment.add("mock.txt",b"Fictional strategy objectives and original business problem.","SA-01")
                data={"answers":{"Q01":"Fictional interview response"},"reviews":{},"edits":{},"title":"Fictional snapshot","persona":"Board","target":4}
                w.assessment.save_workspace(data);w.assessment.snapshot();w.checkpoint(actor)
                self.assertNotIn(b"Fictional interview response",store.current.read_bytes())
            with LocalStore(root,REGISTER,SPEC) as store:
                store.unlock(passphrase);w=DashboardWorkspaceStore(store,aid)
                self.assertEqual(w.assessment.workspace_view()["answers"],data["answers"]);self.assertEqual(w.assessment.workspace_view()["target"],4);self.assertEqual(w.assessment.snapshots[0]["target"],4)
                self.assertEqual(w.assessment.workspace_view()["snapshots"][0]["title"],"Fictional snapshot")
                self.assertEqual(w.assessment.source(f["digest"])["digest"],f["digest"])
                self.assertEqual(store.dp.db.execute("SELECT count(*) FROM sessions").fetchone()[0],0)
                self.assertTrue(w.assessment.calculate({},data["answers"])["productionLocked"])
    def test_refuses_old_workbench(self):
        with tempfile.TemporaryDirectory() as tmp:
            with LocalStore(Path(tmp)/"vault",REGISTER,SPEC) as store:
                aid=store.initialize(secrets.token_urlsafe(24),{r:(r,secrets.token_urlsafe(20)) for r in ROLES})
                with self.assertRaises(Exception):DashboardWorkspaceStore(store,aid)
