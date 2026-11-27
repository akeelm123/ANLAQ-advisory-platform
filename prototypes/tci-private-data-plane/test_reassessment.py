"""Synthetic longitudinal comparison and immutable period acceptance tests."""
import sqlite3,unittest,secrets,tempfile
from pathlib import Path
import test_executive as ebase
import test_validation_workflow as base
from data_plane import DataPlane,Invalid,Denied

class ReassessmentTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"period.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC,enable_pilot_scoring=True)
    cls.tokens={};cls.ids={}
    for name in ["assessor","reviewer","reviewer2","owner","contributor","contributor2","other"]:
        pw=secrets.token_urlsafe(24);cls.ids[name]=cls.dp.bootstrap_user(name,pw);cls.tokens[name]=cls.dp.login(name,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):
    ebase.ExecutiveTests.setUp(self);self.r=self.dp.reassessment
 t=base.ValidationTests.t
 source=base.ValidationTests.source
 body=base.ValidationTests.body
 draft=base.ValidationTests.draft
 accept=base.ValidationTests.accept
 validated=ebase.ExecutiveTests.validated
 brief_body=ebase.ExecutiveTests.brief_body
 brief=ebase.ExecutiveTests.brief
 def snap(self,start="2026-01-01",end="2026-03-31",basis="Fictional population FY26",label="Synthetic period"):
    return self.r.capture(self.t("assessor"),self.a,start,end,label,basis)
 def review(self,id,who="reviewer",decision="accept",confirmed=True):return self.r.review_snapshot(self.t(who),self.a,id,decision,"Synthetic period review",confirmed)
 def follow(self,basis="Fictional population FY26"):
    id=self.snap("2026-04-01","2026-06-30",basis,"Follow-up");self.review(id);return id
 def compare(self,b,f,actions=(),confirmed=True):return self.r.compare(self.t("assessor"),self.a,b,f,"Fictional comparative rationale",confirmed,list(actions))
 def accept_comparison(self,id,who="reviewer",confirmed=True):return self.r.review_comparison(self.t(who),self.a,id,"accept","Synthetic independent comparison",confirmed)
 def view(self):return self.r.view(self.t("owner"),self.a)
 def record(self,id):return next(x for x in self.view()["snapshots"] if x["id"]==id)
 def result(self,id):return next(x for x in self.view()["comparisons"] if x["id"]==id)
 def test_condition_vs_support_and_historical_trace(self):
    v1,r1,d1=self.validated("Q01","not_met");v2,r2,d2=self.validated("Q02","met");v3,_,_=self.validated("Q03","met")
    b=self.snap();self.review(b)
    r,_=self.source("Q01",text="Fictional changed outcome",document=d1["documentId"]);self.accept(self.draft("Q01",[r],condition="met"),[r])
    self.source("Q02",text="Fictional unvalidated replacement",document=d2["documentId"])
    r,_=self.source("Q03",text="Fictional adverse follow-up");self.accept(self.draft("Q03",[r],condition="not_met"),[r])
    self.validated("Q04");f=self.follow();cid=self.compare(b,f);self.accept_comparison(cid)
    result=self.result(cid)["payload"]["result"];changes={x["criterion"]:x["change"] for x in result["criteria"]}
    self.assertEqual([changes[q] for q in ("Q01","Q02","Q03","Q04","Q05")],["condition_improved","support_lost","condition_deteriorated","support_gained","unresolved_both"])
    self.assertEqual(len(result["dimensions"]),7);self.assertIsNone(result["pilot"]);self.assertEqual(self.record(b)["status"],"accepted");self.assertFalse(self.record(b)["matchesCurrent"]);self.assertEqual(result["criteria"][0]["baseline"]["refs"][0]["quote"],r1["quote"])
 def test_period_order_basis_and_draft_staleness(self):
    for start,end in [("bad","2026-01-01"),("2026-03-01","2026-01-01")]:
      with self.assertRaises(Invalid):self.snap(start,end)
    b=self.snap();self.review(b);f=self.follow("Different population")
    with self.assertRaises(Invalid):self.compare(b,f)
    overlap=self.snap("2026-03-31","2026-04-30");self.review(overlap)
    with self.assertRaises(Invalid):self.compare(b,overlap)
    with self.assertRaises(Invalid):self.compare(overlap,b)
    draft=self.snap();self.dp.mark_request(self.t("assessor"),self.a,"SA-01","requested","Synthetic")
    self.assertEqual(self.record(draft)["status"],"draft_superseded")
    with self.assertRaises(Invalid):self.review(draft)
 def test_snapshot_preview_and_independent_comparison(self):
    _,ref,_=self.validated();b=self.snap()
    with self.assertRaises(Invalid):self.review(b,"reviewer2")
    self.review(b);f=self.follow()
    with self.assertRaises(Invalid):self.compare(b,f,confirmed=False)
    c=self.compare(b,f)
    with self.assertRaises(Invalid):self.accept_comparison(c,"reviewer2")
    self.dp.download(self.t("reviewer2"),self.a,ref["versionId"]);self.accept_comparison(c,"reviewer2")
    self.assertEqual(self.result(c)["status"],"accept")
 def test_action_closure_requires_supported_followup(self):
    vid,_,_=self.validated();bref=self.brief([vid]);self.e.review(self.t("reviewer"),self.a,bref,"accept","Synthetic",True);self.e.direction(self.t("owner"),self.a,bref,"Reassess","Synthetic","Synthetic",True)
    b=self.snap();self.review(b);aid=self.record(b)["payload"]["state"]["executive"]["actions"][0]["id"]
    nextvid,_,_=self.validated("Q02");f=self.follow()
    with self.assertRaises(Invalid):self.compare(b,f)
    item={"actionId":aid,"status":"closed","rationale":"Synthetic closure","findingIds":[]}
    with self.assertRaises(Invalid):self.compare(b,f,[item])
    with self.assertRaises(Invalid):self.compare(b,f,[item|{"findingIds":["unknown"]}])
    cid=self.compare(b,f,[item|{"findingIds":[nextvid]}]);self.accept_comparison(cid);self.assertEqual(self.result(cid)["payload"]["actions"][0]["status"],"closed")
 def test_complete_pilot_deltas(self):
    for q in self.dp.rules:
      v,_,_=self.validated(q);sid=self.dp.scoring.draft(self.t("assessor"),self.a,q,v,3,"Synthetic anchor",False,"");self.dp.scoring.review(self.t("reviewer"),self.a,sid,"accept","Synthetic",True,False)
    b=self.snap();self.review(b)
    for q in self.dp.rules:
      vid,_=self.dp.scoring._current_validation(self.a,q);sid=self.dp.scoring.draft(self.t("assessor"),self.a,q,vid,4,"Synthetic sustained outcome",True,"");self.dp.scoring.review(self.t("reviewer"),self.a,sid,"accept","Synthetic",True,True)
    f=self.follow();c=self.compare(b,f);self.accept_comparison(c);p=self.result(c)["payload"]["result"]["pilot"]
    self.assertEqual(float(p["delta"]),1.0);self.assertTrue(p["provisional"]);self.assertEqual(len(p["dimensions"]),7)
 def test_role_isolation_and_immutable_snapshot(self):
    b=self.snap()
    with self.assertRaises(Denied):self.r.view(self.t("contributor"),self.a)
    with self.assertRaises(Denied):self.r.view(self.t("other"),self.a)
    with self.assertRaises(Denied):self.r.review_snapshot(self.t("assessor"),self.a,b,"accept","Synthetic",True)
    with self.assertRaises(Invalid):self.compare(b,b)
    self.review(b);f=self.follow();cid=self.compare(b,f)
    with self.assertRaises(Denied):self.r.review_comparison(self.t("owner"),self.a,cid,"accept","Synthetic",True)
    with self.assertRaises(sqlite3.IntegrityError):
      with self.dp.db:self.dp.db.execute("UPDATE reassessment_snapshots SET payload='changed' WHERE id=?",(b,))
    row=self.dp.db.execute("SELECT payload FROM reassessment_snapshots WHERE id=?",(b,)).fetchone();self.assertNotIn("Fictional population",row["payload"])
    self.assertTrue(self.dp.verify_audit())
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
if __name__=="__main__":unittest.main()
