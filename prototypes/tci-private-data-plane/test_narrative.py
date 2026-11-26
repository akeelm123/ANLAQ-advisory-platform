import json,os,unittest
from pathlib import Path
from extraction import load_schema
from narrative import prepare,verify_proposals,extract_narrative,NarrativeUnavailable
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rules,_=load_schema(HERE/"extraction-schema.json",SPEC.read_bytes())
class NarrativeTests(unittest.TestCase):
 def base(self):
    rule=rules["Q26"];raw=b"Realised value was SGD 4000.\nForecast SGD 2000 is not realised value.";_,segments=prepare("synthetic.txt",raw)
    return rule,raw,segments
 def test_valid_exact_spans(self):
    r,_,s=self.base();q=verify_proposals(r,s,{"proposals":[{"fieldKey":"actual_realised_outcome","segmentId":"S001","quote":"SGD 4000"},{"fieldKey":"forecast_separately","segmentId":"S002","quote":"SGD 2000"}]})
    self.assertEqual(q["counts"]["candidate"],2);f=next(x for x in q["fields"] if x["key"]=="actual_realised_outcome");self.assertEqual(f["citations"][0]["location"],"Text line 1");c=f["citations"][0];self.assertEqual(c["excerpt"][c["startColumn"]-1:c["endColumn"]],c["value"])
 def test_reject_fabricated_wrong_segment_unknown_field(self):
    r,_,s=self.base();p=[{"fieldKey":"actual_realised_outcome","segmentId":"S001","quote":"SGD 9999"},{"fieldKey":"actual_realised_outcome","segmentId":"S002","quote":"SGD 4000"},{"fieldKey":"wrong","segmentId":"S001","quote":"SGD 4000"}]
    q=verify_proposals(r,s,{"proposals":p});self.assertEqual(q["rejectedProposals"],3);self.assertEqual(q["counts"]["candidate"],0)
 def test_repeated_quote_unlocatable(self):
    r=rules["Q26"];_,s=prepare("synthetic.txt",b"SGD 4000 and SGD 4000")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"actual_realised_outcome","segmentId":"S001","quote":"SGD 4000"}]})
    self.assertEqual(q["rejectedProposals"],1)
 def test_conflicting_candidate_stays_unresolved(self):
    r=rules["Q26"];_,s=prepare("synthetic.txt",b"Ledger says SGD 4000.\nReport says SGD 7000.")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"actual_realised_outcome","segmentId":"S001","quote":"SGD 4000"},{"fieldKey":"actual_realised_outcome","segmentId":"S002","quote":"SGD 7000"}]})
    f=next(x for x in q["fields"] if x["key"]=="actual_realised_outcome");self.assertEqual(f["status"],"ambiguous");self.assertIsNone(f["value"])
 def test_invalid_schema_fails_closed(self):
    r,_,s=self.base()
    for p in [{},{"proposals":"invalid"},{"proposals":[{}]*81}]:
        with self.assertRaises(NarrativeUnavailable):verify_proposals(r,s,p)
 def test_model_unavailable_no_fallback(self):
    r,raw,_=self.base()
    def unavailable(*args):raise NarrativeUnavailable("offline")
    with self.assertRaises(NarrativeUnavailable):extract_narrative("synthetic.txt",raw,r,unavailable)
 def test_verified_span_does_not_prove_semantic_correctness(self):
    r,raw,_=self.base()
    def fake(rule,s):return {"proposals":[{"fieldKey":"actual_realised_outcome","segmentId":"S002","quote":"SGD 2000"}]},"synthetic-model"
    result=extract_narrative("synthetic.txt",raw,r,fake)
    # Exact source quote is structurally valid but semantically wrong: cannot be treated as validated.
    self.assertTrue(result["semanticReviewRequired"]);self.assertFalse(result["scoringEligible"]);self.assertEqual(result["status"],"draft")
 def test_window_bound(self):
    with self.assertRaises(NarrativeUnavailable):prepare("synthetic.txt",b"x\n"*81)
if __name__=="__main__":unittest.main(verbosity=2)
