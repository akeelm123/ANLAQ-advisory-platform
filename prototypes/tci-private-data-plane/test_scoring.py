"""Restricted synthetic pilot scoring and workbook arithmetic."""
import json,secrets,tempfile,unittest
from decimal import Decimal
from pathlib import Path
import test_validation_workflow as base
from data_plane import DataPlane,Invalid,Denied
from scoring import weighted_dimensions

class ScoringTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"score.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC,enable_pilot_scoring=True)
    cls.tokens={};cls.ids={}
    for name in ["assessor","reviewer","owner","contributor","contributor2","other"]:
        pw=secrets.token_urlsafe(24);cls.ids[name]=cls.dp.bootstrap_user(name,pw);cls.tokens[name]=cls.dp.login(name,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 setUp=base.ValidationTests.setUp
 t=base.ValidationTests.t
 source=base.ValidationTests.source
 body=base.ValidationTests.body
 draft=base.ValidationTests.draft
 accept=base.ValidationTests.accept
 def validated(self,q="Q01",condition="met"):
    ref,doc=self.source(q,text="Fictional evidence "+q);vid=self.draft(q,[ref],condition=condition);self.accept(vid,[ref]);return vid,ref,doc
 def propose(self,q,vid,n=3,operating=False,flag=""):
    return self.dp.scoring.draft(self.t("assessor"),self.a,q,vid,n,"Fictional anchor rationale",operating,flag)
 def approve(self,id,operating=False):
    return self.dp.scoring.review(self.t("reviewer"),self.a,id,"accept","Fictional independent review",True,operating)
 def view(self):return self.dp.scoring.view(self.t("owner"),self.a)
 def test_calibration_workbook_three_cases(self):
    d=json.loads(Path(__file__).with_name("SCORING-CALIBRATION-FIXTURES.json").read_text())
    self.assertEqual(len(d["cases"]),3)
    for c in d["cases"]:
      with self.subTest(case=c["case"]):self.assertEqual(weighted_dimensions(c["scores"],self.dp.scoring.weights),Decimal(c["exact"]))
    self.assertEqual([Decimal(c["exact"]) for c in d["cases"]],[Decimal("4.11"),Decimal("3.09"),Decimal("1.855")])
 def test_full_28_reviewed_anchors_and_personas(self):
    for q in self.dp.scoring.criteria:
      n=2 if self.dp.scoring.criteria[q]["dimension"]=="Business Value Realisation" else 4
      vid,_,_=self.validated(q,"not_met" if n==2 else "met")
      id=self.propose(q,vid,n,n==4,"Fictional material value risk" if q=="Q25" else "");self.approve(id,n==4)
    v=self.view();self.assertEqual(v["coverage"],28);self.assertEqual(Decimal(v["canonical"]),Decimal("3.6"));self.assertEqual(v["weakestDimensions"],["Business Value Realisation"]);self.assertEqual(len(v["personaLenses"]),4);self.assertEqual(len(v["redFlags"]),1);self.assertTrue(v["finalScoringLocked"])
 def test_missing_not_default_and_adverse(self):
    self.assertIsNone(self.view()["canonical"]);self.assertEqual(self.view()["coverage"],0)
    with self.assertRaises(Invalid):self.propose("Q01","unknown",1)
    vid,_,_=self.validated(condition="not_met")
    for n in [True,0,3,4,6]:
      with self.assertRaises(Invalid):self.propose("Q01",vid,n,True)
    id=self.propose("Q01",vid,1);self.approve(id);self.assertIsNone(self.view()["canonical"]);self.assertEqual(self.view()["coverage"],1)
 def test_review_and_sustained_evidence(self):
    vid,_,_=self.validated()
    with self.assertRaises(Invalid):self.propose("Q01",vid,5)
    id=self.propose("Q01",vid,5,True)
    with self.assertRaises(Invalid):self.approve(id)
    with self.assertRaises(Denied):self.dp.scoring.review(self.t("assessor"),self.a,id,"accept","Synthetic",True,True)
    self.approve(id,True);self.assertEqual(self.view()["coverage"],1)
    with self.assertRaises(Invalid):self.approve(id,True)
 def test_supersession_and_new_validation(self):
    vid,ref,doc=self.validated();i=self.propose("Q01",vid);self.approve(i);self.assertEqual(self.view()["coverage"],1)
    self.source(document=doc["documentId"],text="New fictional source")
    self.assertEqual(self.view()["coverage"],0);self.assertEqual(self.view()["records"][0]["state"],"withheld")
    with self.assertRaises(Invalid):self.propose("Q01",vid)
 def test_new_unreviewed_proposal_withholds_old(self):
    vid,_,_=self.validated();id=self.propose("Q01",vid);self.approve(id);self.propose("Q01",vid,4,True);self.assertEqual(self.view()["coverage"],0)
 def test_roles_and_default_disabled(self):
    for n in ["contributor","other"]:
      with self.assertRaises(Denied):self.dp.scoring.view(self.t(n),self.a)
    s=self.dp.scoring;s.enabled=False
    try:
      self.assertFalse(self.view()["enabled"])
      with self.assertRaises(Denied):self.propose("Q01","unknown")
    finally:s.enabled=True
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
if __name__=="__main__":unittest.main()
