import json,unittest
from serve import REGISTER,SPEC
from simple_scoring import SimpleAssessment
class SimpleTests(unittest.TestCase):
    def setUp(self):
        self.reg=json.loads(REGISTER.read_text());self.spec=json.loads(SPEC.read_text());self.a=SimpleAssessment(self.reg,self.spec)
    def test_exact_weights_and_no_default_score(self):
        r=self.a.calculate({},{});self.assertIsNone(r["draftScore"]);self.assertEqual(r["reviewed"],0);self.assertTrue(r["productionLocked"]);self.assertEqual(sum(self.a.weights.values()),100)
    def test_upload_and_rank_citations(self):
        text=b"Transformation strategy mandate: original business problem and strategy objectives with funded outcomes, sponsor and mandate date."
        f=self.a.add("mock.txt",text);self.assertEqual(self.a.add("mock.txt",text),f)
        r=self.a.analyze();self.assertEqual(len(r["files"]),1);q=next(c for c in r["criteria"] if c["id"]=="Q01")
        self.assertTrue(q["sources"]);self.assertEqual(q["sources"][0]["quote"],text.decode());self.assertEqual(q["sources"][0]["digest"],f["digest"])
        self.assertIsNone(self.a.calculate({"Q01":{"score":5,"confirmed":True,"conflict":False,"operating":False,"rationale":"Mock"}},{"Q01":"Mock answer"})["draftScore"])
    def test_complete_weighted_calculation_and_guards(self):
        for c in self.reg["criteria"]:
            q=c["id"];a=next(a for a in self.reg["responseAnchors"] if a[0]==q and a[1]==3)
            self.a.add(q+".txt",("Fictional "+c["criterion"]+" "+c["question"]+" "+c["minimum"]+" "+a[5]).encode())
            # 20-file limit: combine the remaining sample text in a single file below
            if len(self.a.files)==19:break
        rest=self.reg["criteria"][19:];self.a.add("remaining.txt",("\n".join(c["criterion"]+" "+c["question"]+" "+c["minimum"] for c in rest)).encode())
        rows={c["id"]:{"score":3,"rationale":"Fictional reviewed mock","confirmed":True,"conflict":False,"operating":False} for c in self.reg["criteria"]}
        answers={c["id"]:"Fictional answer" for c in self.reg["criteria"]}
        r=self.a.calculate(rows,answers);self.assertEqual(r["reviewed"],28);self.assertEqual(r["draftScore"],3);self.assertTrue(r["productionLocked"])
        self.a.record_proposals({q:{"score":3} for q in answers},answers)
        self.assertEqual(self.a.calculate({},answers)["unreviewedModelScore"],3)
        changed={**answers,"Q01":"Changed interview"};self.assertIsNone(self.a.calculate({},changed)["unreviewedModelScore"])
        self.a.add("new.txt",b"Fictional new record") if len(self.a.files)<20 else self.a.proposals.clear()
        self.assertIsNone(self.a.calculate({},answers)["unreviewedModelScore"])
        answers.pop("Q01");self.assertIsNone(self.a.calculate(rows,answers)["draftScore"]);answers["Q01"]="Mock answer";rows["Q01"]["conflict"]=True;self.assertIsNone(self.a.calculate(rows,answers)["draftScore"])
if __name__=="__main__":unittest.main()
