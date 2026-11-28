import json,unittest
from serve import REGISTER,SPEC,HERE
from dashboard_logic import DashboardAssessment
from dashboard_parser import parse_dashboard_document,MAX_DASHBOARD_FILE
from document_parser import parse_document,UnsupportedDocument
from dashboard_quality import documentary_flags,operating_context
from simple_ai import verify,prepare
class DashboardV098Tests(unittest.TestCase):
    def setUp(self):
        self.a=DashboardAssessment(json.loads(REGISTER.read_text()),json.loads(SPEC.read_text()))
    def test_larger_dashboard_file_original_limit_unchanged(self):
        data=b"Fictional strategy mandate. "+b" "*300000
        with self.assertRaises(UnsupportedDocument):parse_document("mock.txt",data)
        r=parse_dashboard_document("mock.txt",data);self.assertEqual(r["format"],"txt")
        m=self.a.add("mock.txt",data);self.assertEqual(m["segments"],1)
        with self.assertRaises(UnsupportedDocument):parse_dashboard_document("oversize.txt",b"x"*(MAX_DASHBOARD_FILE+1))
    def test_classification_candidate_not_declaration_and_cache_invalidation(self):
        data=b"Fictional approved business case. Investment scope, assumptions, approval date, benefits, cost, baseline and sign-off."
        doc=self.a.add("unlabelled.txt",data)
        self.assertTrue(any(x["id"]=="SA-02" for x in doc["suggestedRequests"]))
        self.assertEqual(doc["declaredRequests"],[]);self.assertFalse(any(x["declared"] for x in self.a.analyze()["guide"]))
        original=self.a.analyze();original["files"][0]["name"]="changed copy"
        self.assertEqual(self.a.analyze()["files"][0]["name"],"unlabelled.txt")
        self.a.tag(doc["digest"],"SA-02");self.assertTrue(next(g for g in self.a.analyze()["guide"] if g["id"]=="SA-02")["declared"])
        unrelated=self.a.add("random.txt",b"Fictional banana orange pineapple.")
        self.assertEqual(unrelated["suggestedRequests"],[])
    def test_documentary_conflict_same_period_and_different_period(self):
        x={"digest":"a","quote":"FY26 Q2 actual weekly active usage 70% of eligible population, measured platform usage."}
        y={"digest":"b","quote":"FY26 Q2 actual weekly active usage 80% of eligible population, measured platform usage."}
        self.assertIn("document_numeric_discrepancy_review",documentary_flags([x,y]))
        self.assertEqual(documentary_flags([x,{**y,"quote":y["quote"].replace("Q2","Q3")}]),[])
        self.assertEqual(documentary_flags([x,{**y,"quote":y["quote"].replace("actual","target")}]),[])
        self.a.add("usage-a.txt",x["quote"].encode(),"PC-04");self.a.add("usage-b.txt",y["quote"].encode(),"PC-04")
        item=next(x for x in prepare(self.a,"People & Culture",{"Q13":"Fictional neutral interview response"}) if x["id"]=="Q13")
        r=verify([item],{"results":[{"id":"Q13","score":3,"sourceIds":["1"],"rationale":"Mock candidate"}]})
        self.assertEqual(r["Q13"]["status"],"conflict_review_required")
    def test_high_anchor_requires_explicit_operating_context(self):
        one={"id":"1","quote":"FY26 Q2 actual usage measured 80%."};two={"id":"1","quote":"FY26 Q1 actual usage measured 70%, Q2 measured 80%."}
        self.assertFalse(operating_context([one]));self.assertTrue(operating_context([two]))
        for src,expected in [(one,None),(two,4)]:
            r=verify([{"id":"Q13","sources":[src]}],{"results":[{"id":"Q13","score":4,"sourceIds":["1"],"rationale":"Mock candidate"}]})
            self.assertEqual(r["Q13"]["score"],expected)
    def test_action_priority_weight_scope_and_discrepancy(self):
        answers={"Q13":"Fictional interview"}
        self.a.add("usage.txt",b"FY26 Q2 actual weekly active usage 70% of eligible population.","PC-04")
        self.a.record_proposals({"Q13":{"score":None,"status":"conflict_review_required"}},answers)
        r=self.a.calculate({},answers);plan=r["actionPlan"]
        self.assertEqual(plan[0]["dimension"],"People & Culture")
        self.assertEqual(plan[0]["weightedScope"],10);self.assertIn("possible evidence discrepancies",plan[0]["priorityReason"]);self.assertTrue(plan[0]["dependency"])
        self.assertAlmostEqual(sum(a["weightedScope"] for a in plan if a["horizon"]==30),100)
        self.assertTrue(r["productionLocked"])
