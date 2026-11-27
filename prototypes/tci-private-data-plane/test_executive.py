"""Synthetic executive decision support acceptance checks."""
import secrets,tempfile,unittest,sqlite3
from pathlib import Path
import test_validation_workflow as base
from data_plane import DataPlane,Invalid,Denied

class ExecutiveTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"executive.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC)
    cls.tokens={};cls.ids={}
    for name in ["assessor","reviewer","reviewer2","owner","contributor","contributor2","other"]:
        pw=secrets.token_urlsafe(24);cls.ids[name]=cls.dp.bootstrap_user(name,pw);cls.tokens[name]=cls.dp.login(name,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):
    base.ValidationTests.setUp(self);self.dp.bootstrap_membership(self.a,self.ids["reviewer2"],"reviewer");self.e=self.dp.executive
 t=base.ValidationTests.t
 source=base.ValidationTests.source
 body=base.ValidationTests.body
 draft=base.ValidationTests.draft
 accept=base.ValidationTests.accept
 def validated(self,q="Q01",condition="met"):
    ref,doc=self.source(q,text="Fictional evidence "+q);vid=self.draft(q,[ref],condition=condition);self.accept(vid,[ref]);return vid,ref,doc
 def brief_body(self,links=(),**kw):
    return dict(title="Fictional executive briefing",summary="Synthetic executive synthesis",limitations="Residual gaps require human attention",findingIds=list(links),options=[dict(direction="Correct",rationale="Fictional corrective option",consequences="Fictional resourcing implication"),dict(direction="Reassess",rationale="Fictional evidence gap",consequences="Pause synthetic judgement")],actions=[dict(condition="Fictional condition",owner="Fictional sponsor",followUp="Collect fictional evidence")])|kw
 def brief(self,links=(),**kw):return self.e.draft(self.t("assessor"),self.a,self.brief_body(links,**kw))
 def approve(self,id,who="reviewer",confirmed=True):return self.e.review(self.t(who),self.a,id,"accept","Independent synthetic review",confirmed)
 def direction(self,id,direction="Reassess",confirmed=True):return self.e.direction(self.t("owner"),self.a,id,direction,"Fictional owner rationale","Residual fictional conditions",confirmed)
 def view(self):return self.e.view(self.t("owner"),self.a)
 def record(self,id):return next(b for b in self.view()["briefs"] if b["id"]==id)
 def test_gap_only_review_is_not_substantive_direction(self):
    b=self.brief();self.assertEqual(self.record(b)["state"],"review_pending")
    with self.assertRaises(Invalid):self.direction(b)
    with self.assertRaises(Invalid):self.approve(b,confirmed=False)
    self.approve(b);self.assertEqual(self.record(b)["state"],"reviewed_with_gaps")
    with self.assertRaises(Invalid):self.direction(b,"Correct")
    with self.assertRaises(Invalid):self.direction(b,confirmed=False)
    self.direction(b);self.assertTrue(self.record(b)["directionCurrent"]);self.assertFalse(self.view()["automaticDecision"])
    with self.assertRaises(Invalid):self.direction(b)
 def test_adverse_vs_unknown_and_exact_trace(self):
    vid,ref,_=self.validated(condition="not_met")
    with self.assertRaises(Invalid):self.brief()
    with self.assertRaises(Invalid):self.brief(["nonexistent"])
    b=self.brief([vid]);s=self.record(b)["payload"]["snapshot"];self.assertEqual(s["supportedCount"],1)
    c=next(c for c in s["criteria"] if c["criterion"]=="Q01");self.assertEqual(c["state"],"supported_not_met");self.assertEqual(c["refs"][0]["quote"],ref["quote"])
    self.assertEqual(s["criteria"][1]["state"],"insufficient");self.assertEqual(len(s["requests"]),32)
    with self.assertRaises(Invalid):self.approve(b,"reviewer2")
    self.dp.download(self.t("reviewer2"),self.a,ref["versionId"]);self.approve(b,"reviewer2")
 def test_complete_28_supported_and_explicit_human_direction(self):
    vids=[]
    for q in self.dp.rules:vids.append(self.validated(q,"not_met" if q=="Q25" else "met")[0])
    self.assertEqual(self.view()["snapshot"]["supportedCount"],28);self.assertTrue(self.view()["snapshot"]["complete"])
    b=self.brief(vids);self.approve(b);self.assertEqual(self.record(b)["state"],"reviewed_complete")
    self.assertIsNone(self.record(b)["direction"])
    self.direction(b,"Correct");self.assertEqual(self.record(b)["direction"]["direction"],"Correct");self.assertTrue(self.view()["productionLocked"])
 def test_source_supersession_and_historical_direction(self):
    vid,_,doc=self.validated();b=self.brief([vid]);self.approve(b);self.direction(b)
    self.source(document=doc["documentId"],text="Replacement fictional source")
    r=self.record(b);self.assertEqual(r["state"],"superseded");self.assertFalse(r["directionCurrent"]);self.assertEqual(r["direction"]["direction"],"Reassess")
    with self.assertRaises(Invalid):self.direction(b)
 def test_new_brief_and_return(self):
    b=self.brief();self.e.review(self.t("reviewer"),self.a,b,"return","Synthetic gap",False);self.assertEqual(self.record(b)["state"],"returned")
    with self.assertRaises(Invalid):self.direction(b)
    b2=self.brief();self.assertEqual(self.record(b)["state"],"superseded");self.approve(b2)
    b3=self.brief();self.assertEqual(self.record(b2)["state"],"superseded")
    with self.assertRaises(Invalid):self.approve(b)
    self.approve(b3)
 def test_material_conflict_reconciliation_invalidates_brief(self):
    vid,ref,_=self.validated();b=self.brief([vid]);self.approve(b)
    i=self.dp.interviews
    a=i.start(self.t("assessor"),self.a,"Synthetic sponsor","1","Sponsor","Scope")
    d=i.start(self.t("assessor"),self.a,"Synthetic delivery","2","Lead","Scope")
    c1=i.record(self.t("assessor"),self.a,a,"Q01","answered","Yes","Fictional",[],[])
    c2=i.record(self.t("assessor"),self.a,d,"Q01","answered","No","Fictional",[],[])
    conflict=i.conflict(self.t("assessor"),self.a,c1,c2,"Fictional contradiction",True)
    self.assertEqual(self.record(b)["state"],"superseded");self.assertEqual(self.view()["snapshot"]["criteria"][0]["state"],"contradiction")
    b2=self.brief();self.dp.validation.conflict_resolution(self.t("reviewer"),self.a,conflict,"Reconciled both fictional accounts",[ref],True)
    self.assertEqual(self.record(b2)["state"],"superseded");self.assertEqual(self.view()["snapshot"]["criteria"][0]["state"],"supported_met")
 def test_request_update_and_latest_validation_invalidate(self):
    b=self.brief();self.dp.mark_request(self.t("assessor"),self.a,"SA-01","requested","Fictional request");self.assertEqual(self.record(b)["state"],"superseded")
    vid,ref,_=self.validated();b2=self.brief([vid]);self.draft("Q01",[ref]);self.assertEqual(self.record(b2)["state"],"superseded")
 def test_role_isolation_and_immutability(self):
    b=self.brief()
    for role in ["contributor","other"]:
      with self.assertRaises(Denied):self.e.view(self.t(role),self.a)
    with self.assertRaises(Denied):self.e.draft(self.t("reviewer"),self.a,self.brief_body())
    with self.assertRaises(Denied):self.e.review(self.t("assessor"),self.a,b,"accept","Fictional",True)
    with self.assertRaises(Denied):self.e.direction(self.t("reviewer"),self.a,b,"Reassess","Fictional","Fictional",True)
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
    r=self.dp.db.execute("SELECT payload FROM executive_briefs WHERE id=?",(b,)).fetchone();self.assertNotIn("Synthetic executive synthesis",r["payload"])
    with self.assertRaises(sqlite3.IntegrityError):
      with self.dp.db:self.dp.db.execute("UPDATE executive_briefs SET payload='changed' WHERE id=?",(b,))
    self.assertTrue(self.dp.verify_audit())
 def test_distinct_options_and_action_fields(self):
    options=self.brief_body()["options"]
    with self.assertRaises(Invalid):self.brief(options=[options[0],options[0]])
    with self.assertRaises(Invalid):self.brief(actions=[])
    with self.assertRaises(Invalid):self.brief(limitations="")
if __name__=="__main__":unittest.main()
