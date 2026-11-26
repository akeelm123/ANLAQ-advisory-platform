import json,unittest
from pathlib import Path
from pilot_preflight import review,REQUIRED,TRUE_REQUIRED
BASE=json.loads(Path(__file__).with_name("pilot-config.example.json").read_text())
class PilotReadiness(unittest.TestCase):
    def test_empty_manifest_fails_closed(self):
        r=review(BASE);self.assertEqual(r["status"],"blocked");self.assertFalse(r["deploymentEnabled"]);self.assertFalse(r["realClientDataEnabled"])
    def test_no_public_evidence_url(self):
        d=json.loads(json.dumps(BASE));d["network"]["publicEvidenceUrls"]=True;self.assertIn("Public evidence URLs must be prohibited",review(d)["blockers"])
    def test_cannot_turn_on_deployment_or_client_data(self):
        d=json.loads(json.dumps(BASE));d["deploymentAuthorised"]=True;d["realClientDataAuthorised"]=True;self.assertEqual(review(d)["status"],"blocked")
    def test_incomplete_evidence_blocked(self):
        d=json.loads(json.dumps(BASE));d["acceptanceEvidence"]["SE-01"]={"status":"reviewed_pass","evidenceRef":"synthetic test record"};self.assertIn("SE-01 independently reviewed evidence outstanding",review(d)["blockers"])
    def test_complete_synthetic_manifest_only_ready_for_review(self):
        d=json.loads(json.dumps(BASE))
        for section,keys in REQUIRED.items():
            for key in keys:d[section][key]=True if (section,key) in TRUE_REQUIRED else "synthetic decision reference"
        d["hosting"]["subprocessorsApproved"]=True;d["ownerApproval"]="synthetic review only"
        d["acceptanceEvidence"]={f"SE-{i:02}":{"status":"reviewed_pass","evidenceRef":"synthetic test","reviewer":"synthetic reviewer"} for i in range(1,13)}
        r=review(d);self.assertEqual(r["status"],"ready_for_formal_review_not_release");self.assertFalse(r["deploymentEnabled"]);self.assertFalse(r["realClientDataEnabled"]);self.assertFalse(r["scoringEnabled"])
    def test_malformed_manifest_fails_closed(self):
        for d in [None,[],{"hosting":None,"network":None}]:
            r=review(d);self.assertEqual(r["status"],"blocked");self.assertFalse(r["deploymentEnabled"])
if __name__=="__main__":unittest.main(verbosity=2)
