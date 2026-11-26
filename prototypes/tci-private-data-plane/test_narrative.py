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
    r=rules["Q26"];_,s=prepare("synthetic.txt",b"Ledger says realised value SGD 4000.\nReport says realised value SGD 7000.")
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
 def test_forecast_not_promoted_to_actual(self):
    r,raw,_=self.base()
    def fake(rule,s):return {"proposals":[{"fieldKey":"actual_realised_outcome","segmentId":"S002","quote":"SGD 2000"}]},"synthetic-model"
    result=extract_narrative("synthetic.txt",raw,r,fake)
    field=next(f for f in result["fields"] if f["key"]=="actual_realised_outcome")
    self.assertEqual(field["status"],"missing");self.assertEqual(result["rejectedProposals"],1)
 def test_explicit_materiality_fallback_and_conflict(self):
    r=rules["Q05"]
    def omitted(*args):return {"proposals":[]},"synthetic-model"
    q=extract_narrative("synthetic.txt",b"The decision was critical to the fictional rollout.",r,omitted)
    f=next(x for x in q["fields"] if x["key"]=="materiality");self.assertEqual(f["status"],"candidate");self.assertIn("critical to the fictional rollout",f["value"]);self.assertTrue(q["explicitMaterialityFallbackUsed"])
    q=extract_narrative("synthetic.txt",b"The decision was critical to the fictional rollout. The decision was not material to the rollout.",r,omitted)
    self.assertEqual(next(x for x in q["fields"] if x["key"]=="materiality")["status"],"ambiguous")
 def test_short_materiality_quote_expanded_to_context(self):
    r=rules["Q05"]
    def short(rule,segments):return {"proposals":[{"fieldKey":"materiality","segmentId":"S001","quote":"critical"}]},"synthetic-model"
    q=extract_narrative("synthetic.txt",b"The decision was critical to the fictional rollout.",r,short)
    f=next(x for x in q["fields"] if x["key"]=="materiality");self.assertEqual(f["status"],"candidate");self.assertIn("critical to the fictional rollout",f["value"])
 def test_explicit_absence_is_not_a_candidate_value(self):
    r=rules["Q13"];_,s=prepare("synthetic.txt",b"The eligible denominator was not provided.")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"eligible_denominator","segmentId":"S001","quote":"eligible denominator was not provided"}]})
    field=next(f for f in q["fields"] if f["key"]=="eligible_denominator");self.assertEqual(field["status"],"missing");self.assertIsNone(field["value"]);self.assertEqual(len(field["absenceCitations"]),1)
 def test_decision_record_reference_not_decision_content(self):
    r=rules["Q08"];raw=b"The committee agreed to revise the rollout. A fictional steering note records the decision."
    def fake(rule,s):return {"proposals":[{"fieldKey":"decision","segmentId":"S001","quote":"A fictional steering note records the decision."}]},"synthetic-model"
    result=extract_narrative("synthetic.txt",raw,r,fake)
    f=next(x for x in result["fields"] if x["key"]=="decision")
    self.assertEqual(f["status"],"candidate");self.assertIn("revise the rollout",f["value"]);self.assertTrue(result["explicitDecisionFallbackUsed"])
 def test_decision_reference_only_remains_missing(self):
    r=rules["Q08"]
    def fake(rule,s):return {"proposals":[{"fieldKey":"decision","segmentId":"S001","quote":"The steering note records a decision."}]},"synthetic-model"
    result=extract_narrative("synthetic.txt",b"The steering note records a decision.",r,fake)
    self.assertEqual(next(x for x in result["fields"] if x["key"]=="decision")["status"],"missing")
 def test_ownership_acceptance_not_data_scope(self):
    r=rules["Q17"];raw=b"The named owner is accountable within the intake workflow. The ownership record confirms accepted responsibility."
    def fake(rule,s):return {"proposals":[{"fieldKey":"scope","segmentId":"S001","quote":"The ownership record confirms accepted responsibility."}]},"synthetic-model"
    result=extract_narrative("synthetic.txt",raw,r,fake)
    f=next(x for x in result["fields"] if x["key"]=="scope");self.assertEqual(f["status"],"candidate");self.assertIn("intake workflow",f["value"]);self.assertTrue(result["explicitScopeFallbackUsed"])
 def test_no_evidence_supplied_is_not_a_value(self):
    r=rules["Q13"];_,s=prepare("synthetic.txt",b"No operational process evidence was supplied.")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"process_evidence","segmentId":"S001","quote":"No operational process evidence was supplied."}]})
    f=next(x for x in q["fields"] if x["key"]=="process_evidence");self.assertEqual(f["status"],"missing");self.assertEqual(len(f["absenceCitations"]),1)
 def test_zero_change_failures_not_evidence_absence(self):
    r=rules["Q22"];_,s=prepare("synthetic.txt",b"No simulated change failures were recorded.")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"change_failures","segmentId":"S001","quote":"No simulated change failures were recorded."}]})
    self.assertEqual(next(x for x in q["fields"] if x["key"]=="change_failures")["status"],"candidate")
 def test_decision_sentence_boundary_excludes_next_sentence(self):
    from narrative import explicit_decision_proposals
    r=rules["Q08"];_,segments=prepare("synthetic.txt",b"A warning was raised. The committee agreed to revise the rollout.")
    proposals=explicit_decision_proposals(r,segments);self.assertEqual(len(proposals),1);self.assertIn("agreed to revise",proposals[0]["quote"])
 def test_dependency_impact_preserves_context(self):
    r=rules["Q23"];_,s=prepare("synthetic.txt",b"It affects one milestone. The milestone was delayed two days.")
    q=verify_proposals(r,s,{"proposals":[{"fieldKey":"impact","segmentId":"S001","quote":"one milestone"}]})
    self.assertIn("affects one milestone",next(f for f in q["fields"] if f["key"]=="impact")["value"])
if __name__=="__main__":unittest.main(verbosity=2)
