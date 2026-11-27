"""Synthetic recovery and access-boundary tests; no real data or deployed infrastructure."""
import os,secrets,tempfile,unittest
from pathlib import Path
from data_plane import DataPlane,Invalid,Denied
from pilot_storage import seal_synthetic,restore_synthetic,write_synthetic_archive
import test_validation_workflow as base

class PilotStorageTests(unittest.TestCase):
 def setUp(self):
    self.tmp=tempfile.TemporaryDirectory();self.now=[1000000];self.clock=lambda:self.now[0]
    self.key,self.audit,self.vault=[secrets.token_bytes(32) for _ in range(3)]
    self.dp=DataPlane(":memory:",self.key,self.audit,base.REGISTER,base.SPEC,clock=self.clock)
    self.a=self.dp.bootstrap_assessment("FICTIONAL tenant","FICTIONAL scope marker","synthetic test only")
    self.tokens={};self.pw={};self.ids={}
    for n in ("contributor","assessor","reviewer","owner"):
      pw=secrets.token_urlsafe(24);uid=self.dp.bootstrap_user(n,pw);self.dp.bootstrap_membership(self.a,uid,n);self.pw[n]=pw;self.ids[n]=uid;self.tokens[n]=self.dp.login(n,pw)
    r=self.dp.upload(self.tokens["contributor"],self.a,"FICTIONAL document marker","synthetic.txt",b"FICTIONAL source bytes",intake={"criterion":"Q01","requestId":"SA-01","sourceOwner":"Fictional owner","period":"Test","sourceVersion":"1","locator":"Text line 1"})
    self.vid=r["versionId"];self.dp.inspect_quarantine(self.tokens["assessor"],self.a,self.vid);self.dp.screen(self.tokens["assessor"],self.a,self.vid,"accepted","Synthetic")
 def tearDown(self):
    self.dp.close();self.tmp.cleanup()
 def seal(self,seconds=120):return seal_synthetic(self.dp,self.vault,seconds,confirmed_synthetic=True)
 def restore(self,archive,**kwargs):
    opts=dict(archive=archive,vault_key=self.vault,evidence_key=self.key,audit_key=self.audit,register=base.REGISTER,spec=base.SPEC,confirmed_synthetic=True,clock=self.clock);opts.update(kwargs);return restore_synthetic(**opts)
 def test_recovery_round_trip_and_sessions_stripped(self):
    blob=self.seal()
    for secret in (b"FICTIONAL tenant",b"FICTIONAL scope marker",b"FICTIONAL document marker",b"FICTIONAL source bytes",self.key,self.vault,self.audit):self.assertNotIn(secret,blob)
    path=write_synthetic_archive(Path(self.tmp.name)/"synthetic.tci",blob)
    self.assertEqual(path.stat().st_mode&0o777,0o600);self.assertEqual(path.read_bytes(),blob)
    r=self.restore(path.read_bytes())
    try:
      with self.assertRaises(Denied):r.list_assessments(self.tokens["owner"])
      t=r.login("reviewer",self.pw["reviewer"]);self.assertEqual(r.download(t,self.a,self.vid),b"FICTIONAL source bytes")
      self.assertTrue(r.verify_audit())
      with self.assertRaises(Denied):r.release(r.login("owner",self.pw["owner"]),self.a)
    finally:r.close()
 def test_archive_authentication_and_keys(self):
    blob=self.seal()
    for kw in ({"vault_key":secrets.token_bytes(32)},{"evidence_key":secrets.token_bytes(32)},{"audit_key":secrets.token_bytes(32)},{"confirmed_synthetic":False}):
      with self.assertRaises(Invalid):self.restore(blob,**kw)
    with self.assertRaises(Invalid):self.restore(blob[:-1])
 def test_expiry_and_confirmation(self):
    with self.assertRaises(Invalid):seal_synthetic(self.dp,self.vault,120)
    for n in (0,30*86400+1,True):
      with self.assertRaises(Invalid):self.seal(n)
    blob=self.seal(5);self.now[0]+=5
    with self.assertRaises(Invalid):self.restore(blob)
 def test_no_overwrite_and_revoked_membership_preserved(self):
    self.dp.revoke_membership(self.tokens["owner"],self.a,self.ids["contributor"])
    blob=self.seal();p=write_synthetic_archive(Path(self.tmp.name)/"synthetic.tci",blob)
    with self.assertRaises(FileExistsError):write_synthetic_archive(p,blob)
    r=self.restore(blob)
    try:
      self.assertEqual(r.list_assessments(r.login("contributor",self.pw["contributor"])),[])
      self.assertTrue(r.verify_audit())
    finally:r.close()
 def test_methodology_and_independent_keys(self):
    blob=self.seal();changed=Path(self.tmp.name)/"register.json";changed.write_bytes(base.REGISTER.read_bytes()+b" ")
    with self.assertRaises(Invalid):self.restore(blob,register=changed)
    with self.assertRaises(Invalid):seal_synthetic(self.dp,self.key,1,confirmed_synthetic=True)
 def test_integrated_aurora_recovery(self):
    from aurora_pilot import source_case
    path=os.getenv("TCI_AURORA_WORKBOOK")
    if not path:self.skipTest("Set TCI_AURORA_WORKBOOK to fingerprinted fictional source")
    aid=self.dp.bootstrap_assessment("Fictional recovery tenant","Aurora recovery test","Fictional only")
    for role,u in self.ids.items():self.dp.bootstrap_membership(aid,u,role)
    source_case(self.dp,aid,self.tokens,path)
    r=self.restore(self.seal())
    try:
      owner=r.login("owner",self.pw["owner"])
      self.assertEqual(len(r.interviews.view(owner,aid)["claims"]),30)
      self.assertEqual(len(r.validation.view(owner,aid)["drafts"]),28)
      self.assertEqual(r.executive.view(owner,aid)["briefs"][0]["direction"]["direction"],"Reassess")
      self.assertFalse(r.scoring.view(owner,aid)["enabled"]);self.assertTrue(r.verify_audit())
      with self.assertRaises(Denied):r.executive.view(r.login("contributor",self.pw["contributor"]),aid)
    finally:r.close()
if __name__=="__main__":unittest.main()
