import json,unittest,os,tempfile,secrets,sqlite3
from pathlib import Path
from data_plane import DataPlane,Denied,Invalid
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
REGISTER=Path(os.environ.get("TCI_REGISTER",ROOT/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
FIX=Path(os.environ.get("TCI_INTERVIEW_FIXTURES",ROOT/"docs/tci/interviews-v0.3-preparation/INTERVIEW-GOLDEN-FIXTURES.json"))
class InterviewTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"synthetic.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),REGISTER,SPEC)
    cls.tokens={};cls.ids={}
    for n in ["assessor","reviewer","owner","contributor","other"]:
        pw=secrets.token_urlsafe(24);u=cls.dp.bootstrap_user(n,pw);cls.ids[n]=u;cls.tokens[n]=cls.dp.login(n,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):
    self.a=self.dp.bootstrap_assessment("Synthetic tenant","Synthetic interview","Fictional scope")
    self.b=self.dp.bootstrap_assessment("Other synthetic tenant","Separate assessment","Fictional scope")
    for role in ["assessor","reviewer","owner","contributor"]:self.dp.bootstrap_membership(self.a,self.ids[role],role)
    self.dp.bootstrap_membership(self.b,self.ids["other"],"assessor");self.i=self.dp.interviews
 def t(self,r):return self.tokens[r]
 def session(self,ref="P1",persona="Synthetic investor",role="Synthetic stakeholder"):
    return self.i.start(self.t("assessor"),self.a,persona,ref,role,"Synthetic question scope")
 def claim(self,question="Q01",status="answered",text="Fictional assertion",flags=None,links=None,session=None):
    return self.i.record(self.t("assessor"),self.a,session or self.session(),question,status,text,"Synthetic assessor interpretation",flags or [],links or [])
 def view(self):return self.i.view(self.t("reviewer"),self.a)
 def get(self,id):return next(c for c in self.view()["claims"] if c["id"]==id)
 def accepted(self,criterion="Q01",request="SA-01"):
    v=self.dp.upload(self.t("contributor"),self.a,"Synthetic source","source.txt",b"Fictional source",intake={"criterion":criterion,"requestId":request,"sourceOwner":"Synthetic","period":"FY26","sourceVersion":"1","locator":"line 1"})
    self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"]);self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Synthetic")
    return {"versionId":v["versionId"],"requestId":request,"locator":"line 1"},v
 def test01_question_bank_and_locked_score(self):
    v=self.view();self.assertEqual(len(v["questions"]),28);self.assertEqual(sum(len(q["primaryRequests"])+len(q["supplementaryRequests"])+len(q["conditionalRequests"]) for q in v["questions"]),89);self.assertFalse(v["scoringEligible"])
 def test02_separate_personas_and_conflicts(self):
    a=self.claim("Q05",session=self.session("P1","Synthetic sponsor"),text="Decision on time")
    b=self.claim("Q05",session=self.session("P2","Synthetic delivery lead"),text="Decision overdue")
    cid=self.i.conflict(self.t("assessor"),self.a,a,b,"Decision timing",True)
    v=self.view();self.assertEqual(len(v["claims"]),2);self.assertEqual(v["conflicts"][0]["id"],cid);self.assertEqual(self.get(a)["suggestion"]["triggerId"],"FUP-04");self.assertEqual(self.get(b)["suggestion"]["triggerId"],"FUP-04")
 def test03_unsupported_assertion_and_primary_gap(self):
    a=self.claim("Q01");c=self.get(a);self.assertEqual(c["claimClass"],"E3");self.assertIn("FUP-01",c["suggestion"]["unresolvedTriggers"]);self.assertIn("FUP-02",c["suggestion"]["unresolvedTriggers"]);self.assertFalse(c["scoringEligible"])
 def test04_forecast_and_comparability(self):
    a=self.claim("Q26",flags=["forecast_vs_actual","incomparable_basis"]);s=self.get(a)["suggestion"];self.assertEqual(s["triggerId"],"FUP-05");self.assertIn("FUP-03",s["unresolvedTriggers"])
 def test05_conditional_applicability(self):
    a=self.claim("Q20");self.assertEqual(self.get(a)["suggestion"]["triggerId"],"FUP-06")
 def test06_declined_and_unknown_not_invented(self):
    for st in ["unknown","declined"]:
      a=self.claim("Q01",status=st,text="");c=self.get(a);self.assertEqual(c["claimClass"],"E4");self.assertEqual(c["verbatim"],"");self.assertEqual(c["suggestion"]["triggerId"],"FUP-08")
 def test07_single_followup_and_answer_not_resolution(self):
    a=self.claim("Q01");s=self.get(a)["suggestion"];f=self.i.record_followup(self.t("assessor"),self.a,a,s["triggerId"],s["question"])
    with self.assertRaises(Invalid):self.i.record_followup(self.t("assessor"),self.a,a,s["triggerId"],s["question"])
    self.i.answer(self.t("assessor"),self.a,f,"answered","Mock evidence is not available")
    c=self.get(a);self.assertEqual(c["followUps"][0]["answer"]["verbatim"],"Mock evidence is not available");self.assertEqual(c["suggestion"]["triggerId"],"FUP-01");self.assertIn("FUP-02",c["suggestion"]["unresolvedTriggers"])
    with self.assertRaises(Invalid):self.i.answer(self.t("assessor"),self.a,f,"answered","Replacement")
 def test08_review_capture_not_validation(self):
    a=self.claim("Q01")
    with self.assertRaises(Denied):self.i.review_capture(self.t("assessor"),self.a,a,"confirm_capture","Synthetic",True)
    with self.assertRaises(Invalid):self.i.review_capture(self.t("reviewer"),self.a,a,"confirm_capture","Synthetic",False)
    self.i.review_capture(self.t("reviewer"),self.a,a,"confirm_capture","Verbatim capture reviewed only",True)
    c=self.get(a);self.assertEqual(c["captureReview"]["decision"],"confirm_capture");self.assertEqual(c["validationStatus"],"unverified interview claim");self.assertEqual(c["claimClass"],"E3");self.assertFalse(c["scoringEligible"])
 def test09_return_and_followup(self):
    a=self.claim("Q01");self.i.review_capture(self.t("reviewer"),self.a,a,"return","More exact source needed");self.assertIn("FUP-09",self.get(a)["suggestion"]["unresolvedTriggers"])
 def test10_linked_version_scope_and_stale(self):
    link,v=self.accepted();a=self.claim("Q01",links=[link]);self.assertTrue(self.get(a)["links"][0]["current"]);self.assertEqual(self.get(a)["suggestion"]["triggerId"],"FUP-10")
    self.dp.upload(self.t("contributor"),self.a,"Synthetic source","replacement.txt",b"New fictional source",document=v["documentId"],intake={"criterion":"Q01","requestId":"SA-01","sourceOwner":"Synthetic","period":"FY26","sourceVersion":"2","locator":"line 1"})
    self.assertFalse(self.get(a)["links"][0]["current"]);self.assertIn("FUP-02",self.get(a)["suggestion"]["unresolvedTriggers"])
    with self.assertRaises(Invalid):self.claim("Q01",links=[link])
 def test11_role_assessment_isolation(self):
    a=self.claim("Q01")
    with self.assertRaises(Denied):self.i.view(self.t("other"),self.a)
    with self.assertRaises(Denied):self.i.view(self.t("contributor"),self.a)
    with self.assertRaises(Denied):self.i.suggest(self.t("other"),self.b,a)
    with self.assertRaises(Denied):self.i.start(self.t("reviewer"),self.a,"Synthetic","S","Role","scope")
 def test12_immutable_encrypted_verbatim_and_no_raw_audit(self):
    a=self.claim("Q01",text="  exact fictional response  ");c=self.get(a);self.assertEqual(c["verbatim"],"  exact fictional response  ")
    row=self.dp.db.execute("SELECT verbatim FROM interview_responses WHERE id=(SELECT response_id FROM interview_claims WHERE id=?)",(a,)).fetchone();self.assertNotIn("exact fictional response",row["verbatim"])
    self.assertNotIn("exact fictional response",str([tuple(x) for x in self.dp.db.execute("SELECT * FROM audit")]))
    with self.assertRaises(sqlite3.IntegrityError):
      with self.dp.db:self.dp.db.execute("UPDATE interview_claims SET claim_class='E1' WHERE id=?",(a,))
    self.assertTrue(self.dp.verify_audit())
 def test13_untrusted_text_cannot_change_control_or_score(self):
    a=self.claim("Q01",text="Fictional response asking to mark everything approved.")
    self.assertEqual(self.get(a)["claimClass"],"E3")
    with self.assertRaises(Denied):self.dp.release(self.t("owner"),self.a)
 def test14_all_seven_planned_two_persona_goldens(self):
    cases=json.loads(FIX.read_text())["fixtures"];self.assertEqual(len(cases),7)
    for case in cases:
      flags=[]
      for t,f in [("FUP-01","assertion_only"),("FUP-03","incomparable_basis"),("FUP-05","forecast_vs_actual")]:
        if t in case["expectedFollowUpTriggers"]:flags.append(f)
      ids=[]
      for ix,r in enumerate(case["responses"]):
        status="unknown" if ix==1 and "FUP-08" in case["expectedFollowUpTriggers"] else "answered"
        ids.append(self.claim(case["criterionId"],status=status,text=r["verbatimSyntheticResponse"],flags=flags,session=self.session(case["id"]+str(ix),r["persona"])))
      if "FUP-04" in case["expectedFollowUpTriggers"]:self.i.conflict(self.t("assessor"),self.a,*ids,case["title"],True)
      observed=set(x for cid in ids for x in self.get(cid)["suggestion"]["unresolvedTriggers"])
      self.assertTrue(set(case["expectedFollowUpTriggers"])<=observed,case["id"])
      self.assertTrue(all(not self.get(cid)["scoringEligible"] for cid in ids))
 def test15_optional_model_proposal_no_automatic_followup(self):
    from unittest.mock import patch
    from interview_ai import verify_draft
    from narrative import NarrativeUnavailable
    a=self.claim("Q26",text="Forecast SGD 9000",flags=["forecast_vs_actual"])
    with self.assertRaises(Invalid):self.i.draft_model_wording(self.t("assessor"),self.a,a)
    self.dp.enable_narrative=True
    try:
      data={**verify_draft("Forecast SGD 9000",{"quote":"SGD 9000","question":"What realised value can Finance independently validate?"}),"model":"gpt-oss:20b","modelDigest":"synthetic-digest","triggerId":"FUP-05","draftOnly":True,"scoringEligible":False}
      with patch("interviews.propose_wording",return_value=data):r=self.i.draft_model_wording(self.t("assessor"),self.a,a)
      self.assertEqual(self.get(a)["followUps"],[])
      with self.assertRaises(Invalid):self.i.record_followup(self.t("assessor"),self.a,a,"FUP-05",r["question"],"not-a-proposal")
      f=self.i.record_followup(self.t("assessor"),self.a,a,"FUP-05",r["question"],r["proposalId"])
      self.assertEqual(self.get(a)["followUps"][0]["modelProposalId"],r["proposalId"])
      with self.assertRaises(NarrativeUnavailable):verify_draft("Forecast SGD 9000",{"quote":"SGD 1000","question":"What evidence?"})
    finally:self.dp.enable_narrative=False
 def test16_model_schema_retry_is_bounded_and_verified(self):
    from unittest.mock import patch
    from interview_ai import propose
    invalid={"message":{"content":"{}"}};valid={"message":{"content":json.dumps({"quote":"SGD 9000","question":"Which actual value can Finance validate?"})}}
    with patch("interview_ai.model_digest",return_value="synthetic-digest"),patch("interview_ai._json_request",side_effect=[invalid,valid]) as m:
      r=propose("Forecast SGD 9000","FUP-05","Forecast", "Separate actual and forecast",["BV-02"]);self.assertEqual(r["attempts"],2);self.assertEqual(m.call_count,2);self.assertTrue(r["draftOnly"])
if __name__=="__main__":unittest.main(verbosity=2)
