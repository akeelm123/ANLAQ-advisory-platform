import json,unittest
from serve import REGISTER,SPEC
from dashboard_logic import DashboardAssessment
class DashboardTests(unittest.TestCase):
    def setUp(self):
        self.reg=json.loads(REGISTER.read_text());self.spec=json.loads(SPEC.read_text());self.a=DashboardAssessment(self.reg,self.spec)
    def test_guidance_is_optional_and_declaration_not_validation(self):
        m=self.a.metadata();self.assertEqual(len(m["documentGuide"]),32)
        self.assertEqual(sum(m["weights"].values()),100)
        self.assertEqual(len(m["personaWeights"]),4)
        doc=b"Fictional transformation strategy mandate: original business problem and strategy objectives with funded outcomes."
        self.a.add("mock.txt",doc)
        self.assertFalse(any(g["declared"] for g in self.a.analyze()["guide"]))
        self.a.add("mock.txt",doc,"SA-01")
        self.assertTrue(next(g for g in self.a.analyze()["guide"] if g["id"]=="SA-01")["declared"])
        self.assertEqual(len(self.a.files),1)
        with self.assertRaises(ValueError):self.a.add("bad.txt",b"mock","UNKNOWN")
        self.assertIsNone(self.a.calculate({}, {})["draftScore"])
    def test_no_evidence_plan_not_failure(self):
        r=self.a.calculate({},{});self.assertIsNone(r["draftScore"])
        self.assertEqual(len(r["actionPlan"]),14)
        self.assertEqual({a["horizon"] for a in r["actionPlan"]},{30,180})
        self.assertTrue(all(a["type"]!="Remediation / improvement" for a in r["actionPlan"]))
        self.assertTrue(all(a["criteria"] and a["owner"] for a in r["actionPlan"]))
    def test_reviewed_weak_plan_and_candidate_caution(self):
        c=self.reg["criteria"][0];q=c["id"];self.a.add("mock.txt",(c["criterion"]+" "+c["question"]+" "+c["minimum"]).encode())
        answer={q:"Fictional answer"};self.a.record_proposals({q:{"score":2}},answer)
        r=self.a.calculate({},answer);conditional=next(a for a in r["actionPlan"] if a["horizon"]==90);self.assertEqual(conditional["type"],"Conditional improvement");self.assertIn("if independently verified",conditional["action"])
        self.assertTrue(any("tentative lower anchors" in a["action"] for a in r["actionPlan"]))
        row={q:{"score":2,"sourceIds":["1"],"rationale":"Reviewed fictional deficiency","confirmed":True,"conflict":False,"operating":False}}
        r=self.a.calculate(row,answer);a=next(a for a in r["actionPlan"] if a["horizon"]==90)
        self.assertEqual(a["criteria"],[q]);self.assertEqual(a["priority"],"High");self.assertEqual(a["owner"],c["stakeholder"])
        self.assertTrue(r["productionLocked"])
    def test_complete_persona_calculation(self):
        for c in self.reg["criteria"]:
            self.a.add(c["id"]+".txt",(c["criterion"]+" "+c["question"]+" "+c["minimum"]).encode())
        answers={c["id"]:"Fictional answer" for c in self.reg["criteria"]}
        rows={c["id"]:{"score":3,"sourceIds":["1"],"rationale":"Fictional reviewed example","confirmed":True,"conflict":False,"operating":False} for c in self.reg["criteria"]}
        r=self.a.calculate(rows,answers);self.assertEqual(r["draftScore"],3)
        self.assertTrue(all(x["score"]==3 for x in r["personaScores"].values()))
        self.assertEqual(len([x for x in r["actionPlan"] if x["horizon"]==90]),7)
    def test_fictional_example_no_overwrite_and_snapshot_source_binding(self):
        from serve import HERE
        fixture=json.loads((HERE/"narrative-fixtures.json").read_text())["fixtures"]
        r=self.a.load_example(fixture);self.assertEqual(len(r["analysis"]["files"]),28)
        self.assertEqual(len(r["workspace"]["answers"]),28)
        with self.assertRaises(ValueError):self.a.load_example(fixture)
        self.a.snapshot();saved=self.a.snapshots[0];self.assertEqual(len(saved["inputDigests"]),28)
        self.assertIsNone(saved["result"]["draftScore"])
        self.a.workspace["title"]="Changed";self.assertNotEqual(saved["title"],self.a.workspace["title"])
    def test_tag_hint_not_automatic_support_and_review_refs_required(self):
        self.a.add("irrelevant.txt",b"Fictional banana orange pineapple.","SA-01")
        q=next(x for x in self.a.analyze()["criteria"] if x["id"]=="Q01");self.assertEqual(q["sources"],[])
        c=self.reg["criteria"][0];self.a.add("relevant.txt",(c["criterion"]+" "+c["question"]+" "+c["minimum"]).encode(),"SA-01")
        row={"score":3,"rationale":"Mock","confirmed":True,"conflict":False,"operating":False}
        answers={"Q01":"Mock answer"}
        self.assertEqual(self.a.calculate({"Q01":row},answers)["reviewed"],0)
        self.assertEqual(self.a.calculate({"Q01":{**row,"sourceIds":["99"]}},answers)["reviewed"],0)
        r=self.a.calculate({"Q01":{**row,"sourceIds":["1"]}},answers);self.assertEqual(r["reviewed"],1)
        self.assertEqual(len(r["criterionResults"][0]["sourceRefs"]),1)
    def test_actual_interview_measurement_discrepancy_guard(self):
        from simple_ai import prepare,verify
        self.a.add("usage.txt",b"Q2 weekly active usage: 70% of the same eligible population. Actual usage metric from platform.","PC-04")
        items=prepare(self.a,"People & Culture",{"Q13":"Q2 weekly active usage was 80% of the same eligible population."})
        q=next(x for x in items if x["id"]=="Q13");self.assertIn("possible_numeric_difference_check_basis",q["reviewFlags"])
        r=verify([q],{"results":[{"id":"Q13","score":4,"sourceIds":["1"],"rationale":"Mock model candidate"}]})
        self.assertIsNone(r["Q13"]["score"]);self.assertEqual(r["Q13"]["status"],"conflict_review_required")
        self.a.record_proposals(r,{"Q13":"Q2 weekly active usage was 80% of the same eligible population."})
        plan=self.a.calculate({},{"Q13":"Q2 weekly active usage was 80% of the same eligible population."})["actionPlan"]
        self.assertTrue(any("potential interview/document discrepancies" in x["action"] for x in plan))
