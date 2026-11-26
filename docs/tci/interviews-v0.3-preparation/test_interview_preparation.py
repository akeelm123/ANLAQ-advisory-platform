import hashlib,json,os,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent.parent
R=Path(os.environ.get("TCI_REGISTER",ROOT/"docs/tci/methodology/TCI_Master_Evidence_Register_v1.0-reconstructed-rc.1.json"))
S=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
D=json.loads((HERE/"INTERVIEW-SPEC-v0.3-preparation.json").read_text());r=json.loads(R.read_bytes());s=json.loads(S.read_bytes())
class PreparationTests(unittest.TestCase):
 def test_exact_baseline_hashes(self):
    self.assertEqual(D["registerSha256"],hashlib.sha256(R.read_bytes()).hexdigest());self.assertEqual(D["validationSpecSha256"],hashlib.sha256(S.read_bytes()).hexdigest())
 def test_exact_question_wording_and_role(self):
    cards={x["questionId"]:x for x in D["cards"]};self.assertEqual(len(cards),28);self.assertEqual(len(D["cards"]),28)
    for c in r["criteria"]:
      a=cards[c["id"]];self.assertEqual(a["question"],c["question"]);self.assertEqual(a["suggestedStakeholder"],c["stakeholder"]);self.assertEqual(a["dimension"],c["dimension"]);self.assertEqual(a["source"],c["source"])
 def test_exact_mappings_and_followups(self):
    cards={x["questionId"]:x for x in D["cards"]}
    for v in s["rules"]:
      a=cards[v["criterionId"]]
      for k,l in [("primary","primaryRequests"),("supplementary","supplementaryRequests"),("conditional","conditionalRequests")]:self.assertEqual(a[l],v[k])
      self.assertEqual(a["targetedFollowUp"],v["followUp"]);self.assertEqual(a["validationRuleId"],v["ruleId"])
    self.assertEqual(sum(len(c["primaryRequests"])+len(c["supplementaryRequests"])+len(c["conditionalRequests"]) for c in cards.values()),89)
 def test_unique_planned_acceptance_ids(self):
    self.assertEqual(len({t["id"] for t in D["followUpTriggers"]}),10);self.assertEqual(len({a["id"] for a in D["acceptanceScenarios"]}),14)
 def test_no_implementation_or_scoring_claim(self):
    self.assertIn("implementation not authorised",D["status"]);self.assertIn("No final scoring",D["controls"]["scoring"])
 def test_seven_planned_golden_cases_cover_dimensions_without_scoring(self):
    f=json.loads((HERE/"INTERVIEW-GOLDEN-FIXTURES.json").read_text())["fixtures"];self.assertEqual(len(f),7);self.assertEqual(len({x["dimension"] for x in f}),7)
    cards={x["questionId"]:x for x in D["cards"]}
    triggers={x["id"] for x in D["followUpTriggers"]}
    for x in f:
      c=cards[x["criterionId"]];self.assertEqual(x["question"],c["question"]);self.assertEqual(set(x["requestIds"]),set(c["primaryRequests"]+c["supplementaryRequests"]+c["conditionalRequests"]))
      self.assertTrue(set(x["expectedFollowUpTriggers"])<=triggers);self.assertTrue(x["expectedNoScore"]);self.assertEqual(len(x["responses"]),2)
if __name__=="__main__":unittest.main(verbosity=2)
