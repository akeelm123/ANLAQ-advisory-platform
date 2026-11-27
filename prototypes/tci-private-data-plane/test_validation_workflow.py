"""Synthetic criterion validation acceptance tests. No scores or real evidence."""
import os,json,secrets,tempfile,sqlite3,unittest
from pathlib import Path
from data_plane import DataPlane,Invalid,Denied
ROOT=Path(__file__).resolve().parent.parent.parent
REGISTER=Path(os.environ.get("TCI_REGISTER",ROOT/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))

class ValidationTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"synthetic.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),REGISTER,SPEC)
    cls.tokens={};cls.ids={}
    for name in ["assessor","reviewer","owner","contributor","contributor2","other"]:
        pw=secrets.token_urlsafe(24);cls.ids[name]=cls.dp.bootstrap_user(name,pw);cls.tokens[name]=cls.dp.login(name,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):
    self.a=self.dp.bootstrap_assessment("Synthetic tenant","Fictional validation","Synthetic scope")
    for n in ["assessor","reviewer","owner","contributor","contributor2"]:self.dp.bootstrap_membership(self.a,self.ids[n],"contributor" if n.startswith("contributor") else n)
    self.v=self.dp.validation
 def t(self,n):return self.tokens[n]
 def source(self,q="Q01",request=None,text="Fictional source",who="contributor",owner="Synthetic owner",document=None):
    request=request or self.dp.rules[q]["primary"][0]
    r=self.dp.upload(self.t(who),self.a,"Synthetic source","source.txt",text.encode(),document=document,intake={"criterion":q,"requestId":request,"sourceOwner":owner,"period":"FY26","sourceVersion":"1","locator":"Text line 1"})
    self.dp.inspect_quarantine(self.t("assessor"),self.a,r["versionId"]);self.dp.screen(self.t("assessor"),self.a,r["versionId"],"accepted","Synthetic")
    return {"versionId":r["versionId"],"requestId":request,"locator":"Text line 1","quote":text},r
 def body(self,refs=(),**kw):
    return dict(applicability="applicable",condition="met",evidenceClass="E1",strength="Strong",fieldsVerified=True,comparable=True,materialityReviewed=True,requiresCorroboration=False,documentaryConflict=False,claim="Synthetic finding",rationale="Synthetic rationale",owner="Synthetic owner",followUp="Synthetic follow-up",conditionalApplies=False,conditionalRationale="AI out of fictional scope",refs=list(refs),claimIds=[],**{})|kw
 def draft(self,q="Q01",refs=(),**kw):return self.v.draft(self.t("assessor"),self.a,q,self.body(refs,**kw))
 def state(self,id):return next(d for d in self.v.view(self.t("owner"),self.a)["drafts"] if d["id"]==id)["state"]["state"]
 def accept(self,id,refs,**kw):
    for r in refs:self.dp.download(self.t("reviewer"),self.a,r["versionId"])
    return self.v.review(self.t("reviewer"),self.a,id,"accept","Synthetic independent rationale",dict(confirmed=True,applicabilityConfirmed=True,independenceConfirmed=True,alternativeAccepted=True)|kw)
 def test_all_28_criteria_112_structural_scenarios(self):
    for q in self.dp.rules:
      with self.subTest(criterion=q):
        r,_=self.source(q,text="Synthetic cited evidence for "+q)
        for condition,expected in [("met","supported_met"),("not_met","supported_not_met")]:
          did=self.draft(q,[r],condition=condition);self.assertEqual(self.state(did),"review_pending");self.accept(did,[r]);self.assertEqual(self.state(did),expected)
        self.assertEqual(self.state(self.draft(q,[])),"insufficient")
        self.assertEqual(self.state(self.draft(q,[r],documentaryConflict=True)),"contradiction")
    self.assertFalse(self.v.view(self.t("owner"),self.a)["scoringEligible"])
 def test_exact_quote_and_intake(self):
    r,_=self.source()
    for update in [{"quote":"Nonexistent"},{"locator":"Text line 2"},{"requestId":"SA-02"}]:
      with self.assertRaises(Invalid):self.draft(refs=[r|update])
 def test_insufficient_weak_and_asserted(self):
    r,_=self.source()
    for kw in [{"strength":"Weak"},{"evidenceClass":"E3"},{"evidenceClass":"E4"},{"fieldsVerified":False},{"comparable":False},{"materialityReviewed":False},{"condition":"unknown"}]:
      self.assertEqual(self.state(self.draft(refs=[r],**kw)),"insufficient")
    self.assertEqual(self.state(self.draft(refs=[r],applicability="not_applicable")),"exception_pending")
 def test_review_preview_and_independence(self):
    r,_=self.source();did=self.draft(refs=[r])
    with self.assertRaises(Invalid):self.v.review(self.t("reviewer"),self.a,did,"accept","Synthetic",{"confirmed":True})
    with self.assertRaises(Denied):self.v.review(self.t("assessor"),self.a,did,"accept","Synthetic",{"confirmed":True})
    self.accept(did,[r]);self.assertEqual(self.state(did),"supported_met")
    with self.assertRaises(Invalid):self.accept(did,[r])
 def test_corroboration_distinct(self):
    r,_=self.source();r2,_=self.source(text="Second source",who="contributor2",owner="Another owner");same,_=self.source(text="Second source",who="contributor2",owner="Synthetic owner")
    for refs in [[r],[r,same],[r,r]]:
      self.assertEqual(self.state(self.draft(refs=refs,evidenceClass="E2")),"insufficient")
    did=self.draft(refs=[r,r2],evidenceClass="E2")
    with self.assertRaises(Invalid):self.accept(did,[r,r2],independenceConfirmed=False)
    self.accept(did,[r,r2]);self.assertEqual(self.state(did),"supported_met")
 def test_conditional(self):
    r,_=self.source("Q20")
    for kw in [{"conditionalApplies":True},{"conditionalApplies":None},{"conditionalRationale":""}]:
      self.assertEqual(self.state(self.draft("Q20",[r],**kw)),"insufficient")
    c,_=self.source("Q20","DC-05",text="Synthetic conditional control")
    did=self.draft("Q20",[r,c],conditionalApplies=True);self.accept(did,[r,c]);self.assertEqual(self.state(did),"supported_met")
 def test_mapped_alternative(self):
    r,_=self.source(request="SA-02");self.assertEqual(self.state(self.draft(refs=[r])),"insufficient")
    did=self.draft(refs=[r],alternativeRationale="Mapped equivalent explained")
    with self.assertRaises(Invalid):self.accept(did,[r],alternativeAccepted=False)
    self.accept(did,[r]);self.assertEqual(self.state(did),"supported_met")
 def test_superseded(self):
    r,doc=self.source();did=self.draft(refs=[r]);self.accept(did,[r]);self.source(document=doc["documentId"],text="Replacement")
    self.assertEqual(self.state(did),"superseded")
    with self.assertRaises(Invalid):self.draft(refs=[r])
 def test_conflict_reconciliation_and_stale(self):
    r,doc=self.source();i=self.dp.interviews
    a=i.start(self.t("assessor"),self.a,"Synthetic sponsor","P1","Sponsor","Scope")
    b=i.start(self.t("assessor"),self.a,"Synthetic lead","P2","Lead","Scope")
    c1=i.record(self.t("assessor"),self.a,a,"Q01","answered","Yes","Synthetic interpretation",[],[])
    c2=i.record(self.t("assessor"),self.a,b,"Q01","answered","No","Synthetic interpretation",[],[])
    f=i.conflict(self.t("assessor"),self.a,c1,c2,"Fictional inconsistency",True)
    did=self.draft(refs=[r],claimIds=[c1,c2]);self.assertEqual(self.state(did),"contradiction")
    with self.assertRaises(Invalid):self.v.conflict_resolution(self.t("reviewer"),self.a,f,"Reconcile",[r],True)
    self.dp.download(self.t("reviewer"),self.a,r["versionId"]);self.v.conflict_resolution(self.t("reviewer"),self.a,f,"Reconcile both accounts using fictional source",[r],True)
    self.assertEqual(self.v.conflict_status(self.a,f),"resolved");self.assertEqual(self.state(did),"review_pending")
    self.accept(did,[r]);self.source(document=doc["documentId"],text="New fictional source")
    self.assertEqual(self.state(did),"contradiction");self.assertEqual(self.v.conflict_status(self.a,f),"resolution superseded")
 def test_record_isolation_and_immutability(self):
    r,_=self.source();did=self.draft(refs=[r])
    for name in ["contributor","other"]:
      with self.assertRaises(Denied):self.v.view(self.t(name),self.a)
    row=self.dp.db.execute("SELECT payload FROM validation_drafts WHERE id=?",(did,)).fetchone();self.assertNotIn("Synthetic finding",row["payload"])
    with self.assertRaises(sqlite3.IntegrityError):
      with self.dp.db:self.dp.db.execute("UPDATE validation_drafts SET payload='changed' WHERE id=?",(did,))
    self.assertTrue(self.dp.verify_audit())
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
if __name__=="__main__":unittest.main()
