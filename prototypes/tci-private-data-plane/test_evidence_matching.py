"""Synthetic benchmark and human-gate tests for evidence passage discovery."""
import json,secrets,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from data_plane import DataPlane,Invalid,Denied
from evidence_matching import verify_model_labels,hints
import test_validation_workflow as base

class MatchingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.tmp=tempfile.TemporaryDirectory();cls.dp=DataPlane(Path(cls.tmp.name)/"matching.sqlite",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC)
    cls.tokens={};cls.ids={}
    for n in ["assessor","reviewer","owner","contributor","contributor2","other"]:
      pw=secrets.token_urlsafe(24);cls.ids[n]=cls.dp.bootstrap_user(n,pw);cls.tokens[n]=cls.dp.login(n,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close();cls.tmp.cleanup()
 def setUp(self):base.ValidationTests.setUp(self);self.m=self.dp.matching
 t=base.ValidationTests.t
 source=base.ValidationTests.source
 body=base.ValidationTests.body
 def claim(self,q,text):
    i=self.dp.interviews;s=i.start(self.t("assessor"),self.a,"Mock stakeholder","S1","Mock","Scope");return i.record(self.t("assessor"),self.a,s,q,"answered",text,"Unverified",[],[])
 def propose(self,q,claim=None,query="",mode="ranked"):return self.m.propose(self.t("assessor"),self.a,q,claim,query,mode)
 def run_record(self,id):return next(r for r in self.m.view(self.t("owner"),self.a)["runs"] if r["id"]==id)
 def review(self,r,c,decision="link",confirmed=True):return self.m.review(self.t("assessor"),self.a,r,c["id"],decision,"Fictional relevance review",confirmed)
 def test_no_source_and_no_relevant_passage(self):
    r=self.run_record(self.propose("Q13"));self.assertEqual(r["acceptedSources"],0);self.assertIn("No accepted",r["reason"])
    self.source("Q13",text="violet cactus"
    );r=self.run_record(self.propose("Q13"));self.assertEqual(r["acceptedSources"],1);self.assertEqual(r["candidates"],[])
 def test_all_seven_dimension_narrative_benchmark(self):
    cases=[("Q01","Strategy objective reduce approval delay","Enterprise strategy objective reduces processing delay"),("Q05","Timely executive decisions","Executive decision approved before required date"),("Q09","Capacity for enterprise scale","Target workload capacity tested at scale"),("Q13","Weekly adoption active usage","Weekly utilisation of active users"),("Q17","Critical data accountable owner","Critical data element ownership accepted by owner"),("Q21","Release predictability and flow","Delivery throughput and release dates measured"),("Q25","Benefits baseline and target","Original benefits baseline and target expectation")]
    for q,claim,passage in cases:
      with self.subTest(q=q):
        ref,_=self.source(q,text=passage+"\nUnrelated gardening note")
        cid=self.claim(q,claim);r=self.run_record(self.propose(q,cid))
        self.assertTrue(r["candidates"]);self.assertEqual(r["candidates"][0]["quote"],passage);self.assertEqual(r["candidates"][0]["versionId"],ref["versionId"]);self.assertEqual(r["candidates"][0]["locator"],"Text line 1");self.assertEqual(r["candidates"][0]["mapping"],"primary")
 def test_numeric_difference_is_only_hint(self):
    ref,_=self.source("Q13",text="Weekly active users: 70% adoption.");cid=self.claim("Q13","Weekly active users: 80% adoption.")
    r=self.run_record(self.propose("Q13",cid));c=r["candidates"][0];self.assertIn("possible_numeric_difference_check_basis",c["hints"])
    self.assertEqual(self.dp.validation.view(self.t("owner"),self.a)["drafts"],[])
 def test_confirmed_match_integrates_but_not_validation(self):
    ref,_=self.source("Q13",text="Weekly active users: 70% adoption.");cid=self.claim("Q13","Weekly active users: 80% adoption.");rid=self.propose("Q13",cid);c=self.run_record(rid)["candidates"][0]
    with self.assertRaises(Invalid):self.review(rid,c)
    self.dp.download(self.t("assessor"),self.a,ref["versionId"])
    with self.assertRaises(Invalid):self.review(rid,c,confirmed=False)
    self.review(rid,c)
    self.assertEqual(self.run_record(rid)["candidates"][0]["state"],"linked")
    with self.assertRaises(Invalid):self.dp.validation.draft(self.t("assessor"),self.a,"Q13",self.body([],matchIds=[c["id"]]))
    id=self.dp.validation.draft(self.t("assessor"),self.a,"Q13",self.body([],condition="not_met",claimIds=[cid],matchIds=[c["id"]]))
    d=next(d for d in self.dp.validation.view(self.t("owner"),self.a)["drafts"] if d["id"]==id)
    self.assertEqual(d["state"]["state"],"review_pending");self.assertEqual(d["payload"]["refs"][0]["quote"],c["quote"]);self.assertEqual(d["payload"]["matchingCandidateIds"],[c["id"]])
    self.dp.download(self.t("reviewer"),self.a,ref["versionId"]);self.dp.validation.review(self.t("reviewer"),self.a,id,"accept","Fictional independent review",{"confirmed":True})
    self.assertEqual(self.dp.validation.view(self.t("owner"),self.a)["drafts"][0]["state"]["state"],"supported_not_met")
 def test_unmapped_candidate_and_supersession(self):
    ref,doc=self.source("Q01",text="Weekly active users: 70% adoption.");cid=self.claim("Q13","Weekly active users: 80% adoption.");rid=self.propose("Q13",cid);c=self.run_record(rid)["candidates"][0]
    self.assertEqual(c["mapping"],"unmapped");self.dp.download(self.t("assessor"),self.a,ref["versionId"])
    with self.assertRaises(Invalid):self.review(rid,c)
    self.review(rid,c,"reject");self.assertEqual(self.run_record(rid)["candidates"][0]["state"],"rejected")
    ref,doc=self.source("Q13",text="Weekly active users: 70% adoption.");rid=self.propose("Q13",cid);c=next(c for c in self.run_record(rid)["candidates"] if c["versionId"]==ref["versionId"])
    self.dp.download(self.t("assessor"),self.a,ref["versionId"]);self.review(rid,c)
    self.source("Q13",text="Replacement version",document=doc["documentId"])
    self.assertEqual(next(c for c in self.run_record(rid)["candidates"] if c["versionId"]==ref["versionId"])["state"],"superseded")
    with self.assertRaises(Invalid):self.dp.validation.draft(self.t("assessor"),self.a,"Q13",self.body([],matchIds=[c["id"]],claimIds=[cid]))
 def test_roles_and_local_model_disabled(self):
    for n in ("contributor","other"):
      with self.assertRaises(Denied):self.m.view(self.t(n),self.a)
    with self.assertRaises(Denied):self.m.propose(self.t("reviewer"),self.a,"Q01")
    with self.assertRaises(Invalid):self.propose("Q01",mode="local_model")
 def test_local_label_schema_and_fallback(self):
    c=[{"id":"known"}];self.assertEqual(verify_model_labels({"labels":[{"id":"known","label":"potential_conflict"}]},c),{"known":"potential_conflict"})
    for bad in [{"labels":[{"id":"invented","label":"potential_support"}]},{"labels":[{"id":"known","label":"validated"}]},{"labels":[{"id":"known","label":"potential_support","quote":"invented"}]}]:
      with self.assertRaises(ValueError):verify_model_labels(bad,c)
    self.source("Q13",text="Weekly active users: 70% adoption")
    self.dp.enable_narrative=True
    try:
      with patch("evidence_matching.local_labels",side_effect=ValueError("Invalid mock model")):r=self.run_record(self.propose("Q13",query="adoption active users",mode="local_model"))
      self.assertEqual(r["model"]["status"],"unavailable_or_invalid");self.assertTrue(r["candidates"])
    finally:self.dp.enable_narrative=False
 def test_model_omission_retries_only_missing_candidate(self):
    from evidence_matching import local_labels
    c=[{"id":"A","quote":"Mock A","context":"Mock A"},{"id":"B","quote":"Mock B","context":"Mock B"}]
    with patch("evidence_matching.model_digest",return_value="mock-digest"),patch("evidence_matching._json_request",side_effect=[{"message":{"content":json.dumps({"labels":[{"id":"A","label":"potential_support"}]})}},{"message":{"content":json.dumps({"labels":[{"id":"B","label":"context_only"}]})}}]) as req:
      labels,digest=local_labels("Mock claim",c)
      self.assertEqual(labels,{"A":"potential_support","B":"context_only"});self.assertEqual(req.call_count,2)
      payload=json.loads(req.call_args_list[1].args[1]["messages"][1]["content"]);self.assertEqual([x["id"] for x in payload["passages"]],["B"])
 def test_seed_matching_preview_has_no_automatic_validation(self):
    from validation_demo import seed_matching_preview
    rid=seed_matching_preview(self.dp,self.a,self.tokens);r=self.run_record(rid)
    self.assertGreaterEqual(r["acceptedSources"],3);self.assertTrue(any("possible_numeric_difference_check_basis" in c["hints"] for c in r["candidates"]));self.assertTrue(all(c["state"]=="proposal" for c in r["candidates"]))
    self.assertEqual(self.dp.validation.view(self.t("owner"),self.a)["drafts"],[])
if __name__=="__main__":unittest.main()
