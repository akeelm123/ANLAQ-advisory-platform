import copy,json,unittest
from calibration_review import HERE,compare
class CalibrationTests(unittest.TestCase):
 def setUp(self):
    self.a=json.loads((HERE/"CALIBRATION-BLIND-TEMPLATE.json").read_text());self.b=copy.deepcopy(self.a)
    for ref,r in (("Mock A",self.a),("Mock B",self.b)):
      r["assessorRef"]=ref
      for row in r["judgements"]:row.update(condition="supported_met",evidenceClass="E1",strength="Strong",citationRefs=["Mock exact source reference"],rationale="Scripted comparison fixture, not human calibration")
 def test_agreement_and_disagreement_are_not_consensus(self):
    self.b["judgements"][0].update(condition="insufficient",evidenceClass="E4",strength="Not assessed",citationRefs=[])
    r=compare(self.a,self.b);self.assertEqual(r["exactAgreementCounts"]["condition"],6);self.assertEqual(len(r["differences"]),1);self.assertFalse(r["consensusApproved"]);self.assertFalse(r["scoringAuthorised"])
 def test_blank_or_same_assessor_rejected(self):
    with self.assertRaises(ValueError):compare(self.a,self.a)
    with self.assertRaises(ValueError):compare(self.a,json.loads((HERE/"CALIBRATION-BLIND-TEMPLATE.json").read_text()))
 def test_no_supported_claim_without_citations(self):
    self.b["judgements"][0]["citationRefs"]=[]
    with self.assertRaises(ValueError):compare(self.a,self.b)
if __name__=="__main__":unittest.main()
