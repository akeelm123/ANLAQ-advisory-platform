import os,unittest,tempfile,sqlite3,hashlib,secrets
from pathlib import Path
from data_plane import DataPlane,Denied,Invalid,MAX_FILE

HERE=Path(__file__).resolve().parent
REGISTER=Path(os.environ.get("TCI_REGISTER",HERE.parent.parent/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
SPEC=Path(os.environ.get("TCI_SPEC",HERE.parent.parent/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
class DataPlaneTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        cls.dbpath=Path(cls.tmp.name)/"synthetic.sqlite"
        cls.key=secrets.token_bytes(32);cls.audit_key=secrets.token_bytes(32);cls.now=[1000000]
        cls.dp=DataPlane(cls.dbpath,cls.key,cls.audit_key,REGISTER,SPEC,lambda:cls.now[0])
        cls.ids={};cls.tokens={}; cls.passwords={}
        for name in ["contributor","contributor2","assessor","reviewer","owner","other"]:
            pw=secrets.token_urlsafe(24);uid=cls.dp.bootstrap_user(name,pw);cls.ids[name]=uid;cls.passwords[name]=pw;cls.tokens[name]=cls.dp.login(name,pw)
    @classmethod
    def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
    def setUp(self):
        self.dp=self.__class__.dp; self.now[0]+=1
        self.a=self.dp.bootstrap_assessment("Synthetic tenant A","Synthetic assessment A","Synthetic scope")
        self.b=self.dp.bootstrap_assessment("Synthetic tenant B","Synthetic assessment B","Synthetic scope")
        for n,r in [("contributor","contributor"),("contributor2","contributor"),("assessor","assessor"),("reviewer","reviewer"),("owner","owner")]:self.dp.bootstrap_membership(self.a,self.ids[n],r)
        self.dp.bootstrap_membership(self.b,self.ids["other"],"assessor")
    def t(self,name):return self.tokens[name]
    def upload(self,name="contributor",raw=b"Synthetic approved business case data",document=None):
        return self.dp.upload(self.t(name),self.a,"Synthetic evidence","case.txt",raw,document)
    def accepted(self,name="contributor",raw=b"Synthetic approved business case data",document=None):
        v=self.upload(name,raw,document);self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"]);self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Synthetic manual screening");return v
    def finding(self,v,cls="E1",strength="Strong",contradiction=False,criterion="Q01",request="SA-01",extra=None):
        return self.dp.draft_finding(self.t("assessor"),self.a,criterion,"Synthetic finding",cls,strength,contradiction,[{"versionId":v["versionId"],"requestId":request,"locator":"synthetic line 1"}]+(extra or []))
    def test01_tenant_permission_and_wrong_identity(self):
        v=self.accepted()
        for token,aid in [(self.t("other"),self.a),(self.t("assessor"),self.b),(self.t("other"),self.b),("invalid",self.a)]:
            with self.assertRaises(Denied):self.dp.download(token,aid,v["versionId"])
        with self.assertRaises(Denied):self.dp.login("assessor","wrong")
    def test02_quarantine_and_rejected_content_unavailable(self):
        v=self.upload()
        with self.assertRaises(Denied):self.dp.download(self.t("reviewer"),self.a,v["versionId"])
        with self.assertRaises(Denied):self.dp.inspect_quarantine(self.t("contributor"),self.a,v["versionId"])
        with self.assertRaises(Invalid):self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Not inspected")
        self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"])
        self.dp.screen(self.t("assessor"),self.a,v["versionId"],"rejected","Synthetic rejection")
        with self.assertRaises(Denied):self.dp.download(self.t("owner"),self.a,v["versionId"])
    def test03_text_limits_and_role(self):
        for name,data in [("case.pdf",b"fake"),("case.txt",b"\xff"),("case.txt",b""),("case.txt",b"a"*(MAX_FILE+1)),("case.txt",b"abc\x00")]:
            with self.assertRaises(Invalid):self.dp.upload(self.t("contributor"),self.a,"Sample",name,data)
        with self.assertRaises(Denied):self.dp.upload(self.t("reviewer"),self.a,"Sample","case.txt",b"synthetic")
    def test04_encryption_digest_immutable_source(self):
        raw=b"unique synthetic evidence";v=self.accepted(raw=raw)
        row=self.dp.db.execute("SELECT * FROM versions WHERE id=?",(v["versionId"],)).fetchone()
        self.assertNotIn(raw,row["ciphertext"]);self.assertEqual(v["sha256"],hashlib.sha256(raw).hexdigest())
        self.assertEqual(self.dp.download(self.t("assessor"),self.a,v["versionId"]),raw)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.dp.db:self.dp.db.execute("UPDATE versions SET filename='changed' WHERE id=?",(v["versionId"],))
    def test05_own_contributor_and_version_access(self):
        v=self.accepted()
        self.assertTrue(self.dp.download(self.t("contributor"),self.a,v["versionId"]))
        with self.assertRaises(Denied):self.dp.download(self.t("contributor2"),self.a,v["versionId"])
        with self.assertRaises(Denied):self.upload("contributor2",document=v["documentId"])
    def test06_screen_self_and_disposition_immutable(self):
        v=self.upload("assessor")
        with self.assertRaises(Denied):self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"])
        v=self.accepted()
        with self.assertRaises(Invalid):self.dp.screen(self.t("assessor"),self.a,v["versionId"],"rejected","Attempted change")
    def test07_independent_review_gate(self):
        f=self.finding(self.accepted())
        with self.assertRaises(Denied):self.dp.review(self.t("assessor"),self.a,f,"accept","Synthetic",True)
        with self.assertRaises(Invalid):self.dp.review(self.t("reviewer"),self.a,f,"accept","Not confirmed",False)
        self.dp.review(self.t("reviewer"),self.a,f,"accept","Synthetic independent review",True)
        self.assertEqual(self.dp.review_state(self.t("owner"),self.a,f),"accept")
        with self.assertRaises(Invalid):self.dp.review(self.t("reviewer"),self.a,f,"return","Attempted overwrite")
    def test08_class_strength_conflict_gates(self):
        for c,s,k in [("E3","Strong",False),("E1","Not assessed",False),("E1","Strong",True),("E2","Strong",False)]:
            f=self.finding(self.accepted(),c,s,k)
            with self.assertRaises(Invalid):self.dp.review(self.t("reviewer"),self.a,f,"accept","Synthetic",True)
            self.dp.review(self.t("reviewer"),self.a,f,"return","Follow-up")
    def test09_two_independent_source_records(self):
        one=self.accepted();two=self.accepted("contributor2",b"Additional independent synthetic source")
        f=self.finding(one,"E2",extra=[{"versionId":two["versionId"],"requestId":"SA-02","locator":"line 1"}])
        self.dp.review(self.t("reviewer"),self.a,f,"accept","Independence manually confirmed for synthetic sources",True)
    def test10_approved_mapping_and_primary(self):
        v=self.accepted()
        with self.assertRaises(Invalid):self.finding(v,request="LC-01")
        f=self.finding(v,request="SA-02")
        with self.assertRaises(Invalid):self.dp.review(self.t("reviewer"),self.a,f,"accept","Primary absent",True)
        f=self.finding(v,criterion="Q04",request="BV-01")
        self.dp.review(self.t("reviewer"),self.a,f,"accept","Allowed cross-dimension mapping",True)
    def test11_scope_cross_assessment_link_denied(self):
        v=self.accepted()
        with self.assertRaises(Denied):self.dp.draft_finding(self.t("other"),self.b,"Q01","Synthetic","E1","Strong",False,[{"versionId":v["versionId"],"requestId":"SA-01","locator":"line 1"}])
    def test12_superseded_versions_invalidate_readiness(self):
        v=self.accepted();f=self.finding(v)
        self.dp.review(self.t("reviewer"),self.a,f,"accept","Synthetic",True)
        v2=self.upload(raw=b"Updated synthetic source",document=v["documentId"])
        self.assertEqual(v2["version"],2)
        self.assertEqual(self.dp.review_state(self.t("owner"),self.a,f),"superseded")
        with self.assertRaises(Invalid):self.finding(v)
    def test13_conditional_workflow_remains_locked(self):
        f=self.finding(self.accepted(),criterion="Q20",request="DC-01")
        with self.assertRaises(Invalid):self.dp.review(self.t("reviewer"),self.a,f,"accept","Applicability still pending",True)
    def test14_access_revocation(self):
        v=self.accepted()
        self.dp.revoke_membership(self.t("owner"),self.a,self.ids["contributor"])
        with self.assertRaises(Denied):self.dp.download(self.t("contributor"),self.a,v["versionId"])
    def test15_session_logout_and_expiry(self):
        token=self.dp.login("reviewer",self.passwords["reviewer"]);v=self.accepted()
        self.dp.logout(token)
        with self.assertRaises(Denied):self.dp.download(token,self.a,v["versionId"])
        token=self.dp.login("reviewer",self.passwords["reviewer"])
        self.now[0]+=1801
        try:
            with self.assertRaises(Denied):self.dp.download(token,self.a,v["versionId"])
        finally:
            self.now[0]-=1801
    def test16_audit_integrity_and_no_raw_content(self):
        v=self.accepted(raw=b"private synthetic body")
        self.dp.download(self.t("reviewer"),self.a,v["versionId"])
        self.assertTrue(self.dp.verify_audit())
        rows=list(self.dp.db.execute("SELECT * FROM audit"))
        self.assertNotIn("private synthetic body",str([tuple(r) for r in rows]))
        with self.assertRaises(sqlite3.IntegrityError):
            with self.dp.db:self.dp.db.execute("DELETE FROM audit WHERE seq=1")
    def test17_release_gates_remain_closed(self):
        for role in ["owner","assessor","reviewer","contributor"]:
            with self.assertRaises(Denied):self.dp.release(self.t(role),self.a)
    def test18_persisted_database_reopen_integrity(self):
        v=self.accepted(raw=b"synthetic persistent record")
        other=DataPlane(self.dbpath,self.key,self.audit_key,REGISTER,SPEC,lambda:self.now[0])
        try:
            self.assertTrue(other.verify_audit())
            self.assertEqual(other.download(self.t("reviewer"),self.a,v["versionId"]),b"synthetic persistent record")
        finally:other.close()
    def test19_hash_mismatch_rejected(self):
        p=Path(self.tmp.name)/"changed.json";p.write_text("{}")
        with self.assertRaises(Invalid):DataPlane(":memory:",self.key,self.audit_key,p,SPEC)

    def test20_extraction_encrypted_immutable_and_scoped(self):
        import json
        fixture=json.loads((HERE/"golden-fixtures.json").read_text())["fixtures"][0]
        raw=fixture["text"].encode();v=self.dp.upload(self.t("contributor"),self.a,"Synthetic extraction source","sample.txt",raw,intake={"criterion":"Q01","requestId":"SA-01","sourceOwner":"Synthetic","period":"FY26","sourceVersion":"1","locator":"line 1"})
        self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"]);self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Synthetic")
        run=self.dp.run_extraction(self.t("assessor"),self.a,v["versionId"],"Q01")
        row=self.dp.db.execute("SELECT ciphertext FROM extraction_runs WHERE id=?",(run,)).fetchone()
        self.assertNotIn(fixture["expected"][0]["value"].encode(),row["ciphertext"])
        with self.assertRaises(Denied):self.dp.list_extractions(self.t("other"),self.a)
        with self.assertRaises(sqlite3.IntegrityError):
            with self.dp.db:self.dp.db.execute("UPDATE extraction_runs SET method='otherwise' WHERE id=?",(run,))
        self.assertEqual(self.dp.list_extractions(self.t("reviewer"),self.a)[0]["result"]["counts"]["present"],5)
        self.assertTrue(self.dp.verify_audit())
    def test21_narrative_disabled_by_default(self):
        with self.assertRaises(Invalid):self.dp.run_extraction(self.t("assessor"),self.a,"missing","Q02","narrative")
    def test22_narrative_benchmark_replay_encrypted_review(self):
        import json
        from unittest.mock import patch
        fixture=json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"][0]
        bench=json.loads((HERE/"NARRATIVE-BENCHMARK-alpha3.json").read_text())["rows"][0]["result"]
        raw=fixture["text"].encode();v=self.dp.upload(self.t("contributor"),self.a,"Synthetic narrative","investment.txt",raw,intake={"criterion":"Q02","requestId":"SA-02","sourceOwner":"Synthetic","period":"FY26","sourceVersion":"1","locator":"line 1"})
        self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"]);self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Synthetic")
        # Replay actual saved local model proposal through service; no network in this test.
        self.dp.enable_narrative=True
        try:
            with patch("data_plane.extract_narrative",return_value=bench) as model:
                run=self.dp.run_extraction(self.t("assessor"),self.a,v["versionId"],"Q02","narrative")
                model.assert_called_once()
            record=next(r for r in self.dp.list_extractions(self.t("reviewer"),self.a) if r["id"]==run)
            self.assertEqual(record["result"]["model"],"gpt-oss:20b");self.assertTrue(record["result"]["semanticReviewRequired"]);self.assertEqual(record["sourceSha256"],v["sha256"]);self.assertFalse(record["result"]["scoringEligible"])
            with self.assertRaises(Invalid):self.dp.review_extraction(self.t("reviewer"),self.a,run,"accept","Synthetic",True)
            self.dp.download(self.t("reviewer"),self.a,v["versionId"])
            self.dp.review_extraction(self.t("reviewer"),self.a,run,"accept","Synthetic reviewer confirms values and context",True)
            self.assertEqual(next(r for r in self.dp.list_extractions(self.t("owner"),self.a) if r["id"]==run)["state"],"accept")
            with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
        finally:self.dp.enable_narrative=False
if __name__=="__main__":unittest.main(verbosity=2)
