"""Source-grounded workbook dry run and independent isolated mock lifecycle test."""
import os,json,secrets,tempfile,unittest
from pathlib import Path
from decimal import Decimal
from data_plane import DataPlane,Denied,Invalid
import test_validation_workflow as base
from aurora_pilot import source_case,HERE

class AuroraPilotTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"synthetic.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC,enable_pilot_scoring=True)
    cls.tokens={};cls.ids={}
    for name in ["assessor","reviewer","owner","contributor","other"]:
      pw=secrets.token_urlsafe(24);cls.ids[name]=cls.dp.bootstrap_user(name,pw);cls.tokens[name]=cls.dp.login(name,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):
    self.a=self.dp.bootstrap_assessment("Synthetic isolated tenant","Fictional pilot test","Synthetic test only")
    for role in ("assessor","reviewer","owner","contributor"):self.dp.bootstrap_membership(self.a,self.ids[role],role)
 def t(self,name):return self.tokens[name]
 def test_source_workbook_dry_run(self):
    path=os.getenv("TCI_AURORA_WORKBOOK")
    if not path:self.skipTest("Set TCI_AURORA_WORKBOOK to the fingerprinted local source workbook")
    r=source_case(self.dp,self.a,self.tokens,path)
    self.assertEqual((r["rows"],r["claims"],r["coveredCriteria"],r["dimensions"],r["supported"]),(29,30,27,7,0))
    self.assertEqual(Decimal(r["calibrationArithmetic"]),Decimal("3.09"));self.assertIsNone(r["pilotScore"])
    v=self.dp.validation.view(self.t("owner"),self.a);self.assertEqual(len(v["drafts"]),28);self.assertTrue(all(d["state"]["state"] in ("insufficient","contradiction") for d in v["drafts"]))
    self.assertEqual(self.dp.validation.conflict_status(self.a,r["conflict"]),"open");self.assertEqual(len(self.dp.list_versions(self.t("owner"),self.a)),0)
    e=self.dp.executive.view(self.t("owner"),self.a)["briefs"][-1];self.assertEqual(e["state"],"reviewed_with_gaps");self.assertEqual(e["direction"]["direction"],"Reassess")
    self.assertEqual(len(self.dp.reassessment.view(self.t("owner"),self.a)["snapshots"]),0)
    self.assertTrue(self.dp.verify_audit())
 def upload_extract(self,fixture,document=None,suffix=""):
    q,req=fixture["criterionId"],fixture["requestId"];text=fixture["text"]+suffix
    v=self.dp.upload(self.t("contributor"),self.a,"MOCK structural test "+q,"mock-"+q+".txt",text.encode(),document=document,intake={"criterion":q,"requestId":req,"sourceOwner":"Mock fixture owner","period":"Mock test period","sourceVersion":"2" if document else "1","locator":"Text fixture"})
    id=v["versionId"];self.dp.inspect_quarantine(self.t("assessor"),self.a,id);self.dp.screen(self.t("assessor"),self.a,id,"accepted","Scripted mock format screening")
    run=self.dp.run_extraction(self.t("assessor"),self.a,id,q);self.dp.download(self.t("reviewer"),self.a,id)
    result=next(x for x in self.dp.list_extractions(self.t("reviewer"),self.a) if x["id"]==run)["result"]
    self.assertEqual(result["counts"]["present"],len(fixture["expected"]));self.assertFalse(result["counts"]["missing"]);self.assertFalse(result["counts"]["ambiguous"])
    for expected in fixture["expected"]:
      field=next(x for x in result["fields"] if x["key"]==expected["key"]);self.assertEqual(field["value"],expected["value"])
    self.dp.review_extraction(self.t("reviewer"),self.a,run,"accept","Scripted fixture exact-field check",True)
    refs=[{"versionId":id,"requestId":req,"locator":"Text line "+str(e["line"]),"quote":e["excerpt"]} for e in fixture["expected"]]
    return v,refs
 def validate_score(self,q,refs,claimids,condition,n):
    body={"applicability":"applicable","condition":condition,"evidenceClass":"E1","strength":"Strong","fieldsVerified":True,"comparable":True,"materialityReviewed":True,"requiresCorroboration":False,"documentaryConflict":False,"claim":"MOCK structural condition, not an Aurora result","rationale":"Scripted fixture control-flow assertion only; no semantic assessment","owner":"Mock owner","followUp":"Mock follow-up","conditionalApplies":False,"conditionalRationale":"Mock AI out of scope","refs":refs,"claimIds":claimids}
    id=self.dp.validation.draft(self.t("assessor"),self.a,q,body);self.dp.validation.review(self.t("reviewer"),self.a,id,"accept","Scripted structural review",{"confirmed":True,"applicabilityConfirmed":True})
    sid=self.dp.scoring.draft(self.t("assessor"),self.a,q,id,n,"Scripted anchor control test",False,"Mock adverse value risk" if n==2 else "")
    self.dp.scoring.review(self.t("reviewer"),self.a,sid,"accept","Scripted anchor review",True,False)
    return id
 def snapshot(self,label,start,end):
    r=self.dp.reassessment;id=r.capture(self.t("assessor"),self.a,start,end,label,"Mock identical population and basis");r.review_snapshot(self.t("reviewer"),self.a,id,"accept","Scripted period review",True);return id
 def test_full_mock_integrated_lifecycle(self):
    fixtures=json.loads((HERE/"golden-fixtures.json").read_text())["fixtures"];refs={};docs={};findings=[];i=self.dp.interviews
    for f in fixtures:
      q=f["criterionId"];docs[q],refs[q]=self.upload_extract(f)
    self.assertEqual(len(self.dp.list_extractions(self.t("owner"),self.a)),28)
    a=i.start(self.t("assessor"),self.a,"Mock Finance","Mock-F","Finance","Separate mock test");b=i.start(self.t("assessor"),self.a,"Mock Programme","Mock-P","Programme","Separate mock test")
    c1=i.record(self.t("assessor"),self.a,a,"Q25","answered","Mock claims condition not met","Scripted conflicting claim",[],[])
    c2=i.record(self.t("assessor"),self.a,b,"Q25","answered","Mock claims condition met","Scripted conflicting claim",[],[])
    conflict=i.conflict(self.t("assessor"),self.a,c1,c2,"Mock contradiction test",True)
    self.assertEqual(self.dp.validation.conflict_status(self.a,conflict),"open")
    self.dp.validation.conflict_resolution(self.t("reviewer"),self.a,conflict,"Mock resolution control test; not actual financial evidence",refs["Q25"],True)
    for q in self.dp.rules:
      adverse=q in ("Q13","Q25");findings.append(self.validate_score(q,refs[q],[c1,c2] if q=="Q25" else [],"not_met" if adverse else "met",2 if adverse else 3))
    score=self.dp.scoring.view(self.t("owner"),self.a);self.assertEqual(score["coverage"],28);self.assertIsNotNone(score["canonical"])
    e=self.dp.executive
    brief=e.draft(self.t("assessor"),self.a,{"title":"MOCK structural full-coverage brief","summary":"Scripted test of supported adverse and met states","limitations":"All inputs are labelled mock fixtures, not Aurora conclusions","findingIds":findings,"options":[{"direction":"Correct","rationale":"Mock corrective option","consequences":"Mock resource implications"},{"direction":"Reassess","rationale":"Mock evidence request option","consequences":"Mock hold"}],"actions":[{"condition":"Mock value condition","owner":"Mock accountable owner","followUp":"Mock follow-up source"}]})
    e.review(self.t("reviewer"),self.a,brief,"accept","Scripted independent brief check",True);e.direction(self.t("owner"),self.a,brief,"Correct","Scripted human-role choice","Mock conditions only",True)
    baseline=self.snapshot("Mock baseline","2026-01-01","2026-03-31")
    f=next(f for f in fixtures if f["criterionId"]=="Q25");_,newrefs=self.upload_extract(f,docs["Q25"]["documentId"],"\nMOCK follow-up revision; no actual assessment\n")
    self.assertEqual(self.dp.validation.conflict_status(self.a,conflict),"resolution superseded");self.assertIsNone(self.dp.scoring.view(self.t("owner"),self.a)["canonical"])
    self.dp.validation.conflict_resolution(self.t("reviewer"),self.a,conflict,"Mock revised resolution",newrefs,True)
    v=self.validate_score("Q25",newrefs,[c1,c2],"met",3);follow=self.snapshot("Mock follow-up","2026-04-01","2026-06-30")
    r=self.dp.reassessment; action=r.view(self.t("owner"),self.a)["snapshots"][0]["payload"]["state"]["executive"]["actions"][0]
    comp=r.compare(self.t("assessor"),self.a,baseline,follow,"Scripted comparable fixture periods",True,[{"actionId":action["id"],"status":"closed","rationale":"Mock source-backed closure test","findingIds":[v]}])
    r.review_comparison(self.t("reviewer"),self.a,comp,"accept","Scripted comparison review",True)
    result=r.view(self.t("owner"),self.a)["comparisons"][0]["payload"]["result"];self.assertEqual(len(result["dimensions"]),7);self.assertEqual(next(c for c in result["criteria"] if c["criterion"]=="Q25")["change"],"condition_improved");self.assertGreater(Decimal(result["pilot"]["delta"]),0)
    self.upload_extract(next(f for f in fixtures if f["criterionId"]=="Q13"),docs["Q13"]["documentId"],"\nMOCK further change\n")
    self.assertIsNone(self.dp.scoring.view(self.t("owner"),self.a)["canonical"]);self.assertEqual(r.view(self.t("owner"),self.a)["snapshots"][0]["status"],"accepted")
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
    with self.assertRaises(Denied):r.view(self.t("contributor"),self.a)
    self.assertTrue(self.dp.verify_audit())
if __name__=="__main__":unittest.main()
