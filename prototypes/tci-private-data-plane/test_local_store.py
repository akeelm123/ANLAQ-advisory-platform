"""Synthetic persistence and recovery controls; no user vault touched."""
import secrets,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from local_store import LocalStore,ROLES
from data_plane import Invalid,Denied
import test_validation_workflow as base

class LocalStoreTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.path=Path(self.tmp.name)/"vault";self.now=[1000000];self.clock=lambda:self.now[0];self.passphrase=secrets.token_urlsafe(24)
    self.accounts={r:(r+"-named",secrets.token_urlsafe(24)) for r in ROLES}
 def tearDown(self):self.tmp.cleanup()
 def store(self,**kw):return LocalStore(self.path,base.REGISTER,base.SPEC,clock=self.clock,**kw)
 def login(self,dp,role):return dp.login(*self.accounts[role])
 def upload(self,dp,aid):
    return dp.upload(self.login(dp,"contributor"),aid,"Fictional metadata marker","source.txt",b"Fictional document bytes",intake={"criterion":"Q01","requestId":"SA-01","sourceOwner":"Synthetic","period":"Test","sourceVersion":"1","locator":"Text line 1"})
 def test_restart_recovery_named_accounts_and_no_session_restore(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);dp=s.dp;old=self.login(dp,"owner");v=self.upload(dp,aid);s.checkpoint()
      self.assertNotIn(b"Fictional metadata marker",s.current.read_bytes());self.assertEqual(s.current.stat().st_mode&0o777,0o600)
      self.assertEqual(s.saltfile.stat().st_mode&0o777,0o600)
    with self.store() as s:
      dp=s.unlock(self.passphrase)
      with self.assertRaises(Denied):dp.list_assessments(old)
      assessor=self.login(dp,"assessor");dp.inspect_quarantine(assessor,aid,v["versionId"]);dp.screen(assessor,aid,v["versionId"],"accepted","Synthetic");s.checkpoint()
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.download(self.login(dp,"reviewer"),aid,v["versionId"]),b"Fictional document bytes");self.assertTrue(dp.verify_audit());self.assertFalse(dp.scoring.view(self.login(dp,"owner"),aid)["enabled"])
 def test_second_instance_and_wrong_passphrase(self):
    with self.store() as s:
      s.initialize(self.passphrase,self.accounts)
      with self.assertRaises(Invalid):self.store()
    with self.store() as s:
      with self.assertRaises(Invalid):s.unlock(secrets.token_urlsafe(24))
    with self.store() as s:s.unlock(self.passphrase)
 def test_no_overwrite_and_duplicate_roles(self):
    with self.store() as s:
      bad=dict(self.accounts);bad["reviewer"]=(bad["assessor"][0],bad["reviewer"][1])
      with self.assertRaises(Invalid):s.initialize(self.passphrase,bad)
      s.initialize(self.passphrase,self.accounts)
      with self.assertRaises(Invalid):s.initialize(self.passphrase,self.accounts)
    with self.store() as s:
      with self.assertRaises(Invalid):s.initialize(self.passphrase,self.accounts)
 def test_atomic_failure_preserves_prior_checkpoint(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);before=s.current.read_bytes();self.upload(s.dp,aid)
      with patch("local_store.os.replace",side_effect=OSError("Synthetic write failure")):
        with self.assertRaises(OSError):s.checkpoint()
      self.assertEqual(before,s.current.read_bytes())
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.list_versions(self.login(dp,"owner"),aid),[])
 def test_revoke_persists_and_backup_no_overwrite(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);dp=s.dp;owner=self.login(dp,"owner");contributor=self.login(dp,"contributor")
      user=dp._actor(contributor,aid,{"contributor"})["id"];dp.revoke_membership(owner,aid,user);s.checkpoint()
      path=Path(self.tmp.name)/"backup.tci";s.backup(path)
      with self.assertRaises(FileExistsError):s.backup(path)
      self.assertTrue(path.exists())
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.list_assessments(self.login(dp,"contributor")),[])
 def test_expired_checkpoint_stays_locked(self):
    with self.store(retention=5) as s:s.initialize(self.passphrase,self.accounts)
    self.now[0]+=5
    with self.store() as s:
      with self.assertRaises(Invalid):s.unlock(self.passphrase)
 def test_directory_and_file_modes(self):
    self.path.mkdir(mode=0o755)
    with self.assertRaises(Invalid):self.store()
    self.path.chmod(0o700)
    with self.store() as s:s.initialize(self.passphrase,self.accounts)
    (self.path/"current.tci").chmod(0o644)
    with self.store() as s:
      with self.assertRaises(Invalid):s.unlock(self.passphrase)
 def test_restore_backup_into_new_vault(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);v=self.upload(s.dp,aid);s.checkpoint()
      path=Path(self.tmp.name)/"backup.tci";s.backup(path)
    recovered=Path(self.tmp.name)/"recovered"
    with LocalStore(recovered,base.REGISTER,base.SPEC,clock=self.clock) as s:
      dp=s.recover_backup(path,self.path/"salt.bin",self.passphrase)
      self.assertEqual(dp.list_versions(self.login(dp,"owner"),aid)[0]["versionId"],v["versionId"])
      with self.assertRaises(Invalid):s.recover_backup(path,self.path/"salt.bin",self.passphrase)
    with LocalStore(recovered,base.REGISTER,base.SPEC,clock=self.clock) as s:
      dp=s.unlock(self.passphrase);self.assertTrue(dp.verify_audit())
 def test_upgrade_v092_checkpoint_preserves_source_and_adds_matching_schema(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);v=self.upload(s.dp,aid)
      # Simulate a synthetic snapshot from before the matching tables existed.
      s.dp.db.executescript("DROP TABLE matching_reviews; DROP TABLE matching_runs;")
      s.checkpoint()
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.list_versions(self.login(dp,"owner"),aid)[0]["versionId"],v["versionId"])
      self.assertEqual(dp.matching.view(self.login(dp,"owner"),aid)["runs"],[])
      run=dp.matching.propose(self.login(dp,"assessor"),aid,"Q01");s.checkpoint()
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.matching.view(self.login(dp,"owner"),aid)["runs"][0]["id"],run);self.assertTrue(dp.verify_audit())
 def test_upgrade_v093_checkpoint_adds_intake_ledger_without_inventing_scan(self):
    with self.store() as s:
      aid=s.initialize(self.passphrase,self.accounts);v=self.upload(s.dp,aid);s.dp.db.executescript("DROP TABLE intake_assurance;");s.checkpoint()
    with self.store() as s:
      dp=s.unlock(self.passphrase);self.assertEqual(dp.list_versions(self.login(dp,"owner"),aid)[0]["versionId"],v["versionId"])
      self.assertEqual(dp.intake_assurance.view(self.login(dp,"owner"),aid)["records"],[])
      dp.intake_assurance.require_scan=True
      assessor=self.login(dp,"assessor");dp.inspect_quarantine(assessor,aid,v["versionId"])
      with self.assertRaises(Invalid):dp.screen(assessor,aid,v["versionId"],"accepted","Synthetic strict screen")
if __name__=="__main__":unittest.main()
