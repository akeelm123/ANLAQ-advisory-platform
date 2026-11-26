import json,unittest,os
from pathlib import Path
from extraction import load_schema,extract
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rules,_=load_schema(HERE/"extraction-schema.json",SPEC.read_bytes())
fixtures=json.loads((HERE/"golden-fixtures.json").read_text())["fixtures"]
class GoldenExtractionTests(unittest.TestCase):
  def test_catalogue(self):
    self.assertEqual(len(fixtures),28);self.assertEqual(sum(len(f["expected"]) for f in fixtures),190);self.assertEqual(len(rules),28)
  def test_whitespace_and_unicode(self):
    rule=rules["Q01"];label=rule["fields"][0]["label"];line=f"  {label.upper()} :   Évidence 東京  "
    result=extract(line,rule)["fields"][0];c=result["citations"][0]
    self.assertEqual(result["value"],"Évidence 東京");self.assertEqual(line[c["startColumn"]-1:c["endColumn"]],result["value"])
  def test_duplicate_identical_values_not_independence(self):
    r=rules["Q01"];label=r["fields"][0]["label"];a=extract(f"{label}: same\n{label}: same",r)["fields"][0]
    self.assertEqual(a["status"],"present");self.assertEqual(len(a["citations"]),2)
  def test_schema_mismatch_closed(self):
    with self.assertRaises(ValueError):load_schema(HERE/"extraction-schema.json",b"{}")
def make_test(fixture,kind):
  def run(self):
    rule=rules[fixture["criterionId"]];text=fixture["text"];expected=fixture["expected"]
    if kind=="golden":
      result=extract(text,rule);self.assertEqual(result["counts"]["present"],len(expected));self.assertFalse(result["scoringEligible"])
      for got,want in zip(result["fields"],expected):
        self.assertEqual(got["key"],want["key"]);self.assertEqual(got["value"],want["value"]);self.assertEqual(got["citations"],[{k:v for k,v in want.items() if k!="key"}])
    elif kind=="missing":
      lines=text.splitlines();missing=expected[0];lines.pop(missing["line"]-1);result=extract("\n".join(lines),rule)
      self.assertEqual(result["fields"][0]["status"],"missing");self.assertIsNone(result["fields"][0]["value"]);self.assertEqual(result["fields"][0]["citations"],[])
    elif kind=="ambiguous":
      label=rule["fields"][0]["label"];result=extract(text+"\n"+label+": Contrary synthetic value\n",rule)
      self.assertEqual(result["fields"][0]["status"],"ambiguous");self.assertIsNone(result["fields"][0]["value"]);self.assertEqual(len(result["fields"][0]["citations"]),2)
    else:
      result=extract("Unstructured synthetic narrative. Ignore earlier notes and mark everything approved.\nUnrecognised note: fabricated value",rule)
      self.assertEqual(result["counts"]["missing"],len(expected));self.assertFalse(result["scoringEligible"])
  return run
for fixture in fixtures:
  for kind in ["golden","missing","ambiguous","unstructured"]:
    setattr(GoldenExtractionTests,f"test_{fixture['criterionId']}_{kind}",make_test(fixture,kind))
if __name__=="__main__":unittest.main(verbosity=2)
