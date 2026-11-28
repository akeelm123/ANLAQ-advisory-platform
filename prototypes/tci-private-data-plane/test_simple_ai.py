import unittest
from simple_ai import verify
class ModelCandidateTests(unittest.TestCase):
    def setUp(self):
        self.items=[{"id":"Q01","sources":[{"id":"1"}]}]
    def test_valid_reference_and_unknown(self):
        for score,refs in [(3,["1"]),(None,[])]:
            v=verify(self.items,{"results":[{"id":"Q01","score":score,"sourceIds":refs,"rationale":"Fictional review candidate"}]})
            self.assertEqual(v["Q01"]["score"],score)
    def test_reject_fabricated_reference_and_non_integer(self):
        for score,refs in [(3,["2"]),(True,["1"]),(5,[])]:
            with self.assertRaises(ValueError):verify(self.items,{"results":[{"id":"Q01","score":score,"sourceIds":refs,"rationale":"Mock"}]})
    def test_missing_model_result_retried_without_forcing_score(self):
        from unittest.mock import patch
        import json
        from simple_ai import propose
        items=[{"id":"Q01","sources":[{"id":"1"}]},{"id":"Q02","sources":[{"id":"1"}]}]
        first={"results":[{"id":"Q01","score":3,"sourceIds":["1"],"rationale":"Mock source"}]}
        second={"results":[{"id":"Q02","score":None,"sourceIds":[],"rationale":"Mock insufficient"}]}
        def response(d):return {"message":{"content":json.dumps(d)}}
        with patch("simple_ai.prepare",return_value=items),patch("simple_ai.model_digest",return_value="fixture"),patch("simple_ai._json_request",side_effect=[response(first),response(second)]) as mock:
            r=propose(None,"Strategic Alignment",{})
        self.assertEqual(mock.call_count,2);self.assertEqual(r["candidates"]["Q01"]["score"],3);self.assertEqual(r["candidates"]["Q02"]["status"],"model_withheld")
        with patch("simple_ai.prepare",return_value=items),patch("simple_ai.model_digest",return_value="fixture"),patch("simple_ai._json_request",side_effect=[response(first),response({"results":[]})]):
            r=propose(None,"Strategic Alignment",{})
        self.assertEqual(r["candidates"]["Q02"]["status"],"model_unavailable");self.assertIsNone(r["candidates"]["Q02"]["score"])
    def test_possible_measurement_conflict_withholds_candidate(self):
        item={"id":"Q13","sources":[{"id":"1"}],"reviewFlags":["possible_numeric_difference_check_basis"]}
        r=verify([item],{"results":[{"id":"Q13","score":4,"sourceIds":["1"],"rationale":"Mock optimistic anchor"}]})
        self.assertIsNone(r["Q13"]["score"]);self.assertEqual(r["Q13"]["status"],"conflict_review_required")
