import secrets,unittest
from data_plane import DataPlane
from validation_demo import seed_validation_demo
import test_validation_workflow as base
class ValidationDemoTests(unittest.TestCase):
 def test_mock_evidence_matches_and_distinguishes_receipt(self):
    dp=DataPlane(":memory:",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC)
    try:
      a=dp.bootstrap_assessment("Mock tenant","MOCK document-backed validation — NOT Aurora","Scripted example");t={}
      for n,r in [("contributor","contributor"),("contributor2","contributor"),("assessor","assessor"),("reviewer","reviewer"),("owner","owner")]:
        pw=secrets.token_urlsafe(24);u=dp.bootstrap_user(n,pw);dp.bootstrap_membership(a,u,r);t[n]=dp.login(n,pw)
      seed_validation_demo(dp,a,t)
      v=dp.validation.view(t["owner"],a);states={d["criterion"]:d["state"]["state"] for d in v["drafts"]}
      self.assertEqual(sum(s=="supported_met" for s in states.values()),5);self.assertEqual(sum(s=="supported_not_met" for s in states.values()),2)
      self.assertEqual(states["Q03"],"insufficient")
      q25=next(d for d in v["drafts"] if d["criterion"]=="Q25");self.assertEqual(q25["payload"]["evidenceClass"],"E2");self.assertEqual(len({r["sourceOwner"] for r in q25["payload"]["refs"]}),2)
      self.assertEqual(len(dp.list_versions(t["owner"],a)),9);self.assertEqual(len(dp.list_extractions(t["owner"],a)),7);self.assertFalse(v["scoringEligible"])
    finally:dp.close()
if __name__=="__main__":unittest.main()
