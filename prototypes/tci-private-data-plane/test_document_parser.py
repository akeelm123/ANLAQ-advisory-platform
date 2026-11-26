import hashlib,json,unittest,zipfile,os
from pathlib import Path
from document_parser import parse_document,extract_document,preview_document,UnsupportedDocument
from extraction import load_schema
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent.parent
SPEC=Path(os.environ.get("TCI_SPEC",ROOT/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
rules,_=load_schema(HERE/"extraction-schema.json",SPEC.read_bytes())
manifest=json.loads((HERE/"golden-document-fixtures.json").read_text())["fixtures"]
class DocumentFixtureTest(unittest.TestCase):
    def test_manifest(self):
        self.assertEqual(len(manifest),21);self.assertEqual(sum(len(x["expected"]) for x in manifest),138)
        self.assertEqual({x["filename"].split(".")[-1] for x in manifest},{"pdf","docx","xlsx"})
    def test_unsupported_formats_and_malformed_documents(self):
        for name,raw in [("data.zip",b"synthetic"),("data.docx",b"synthetic"),("data.pdf",b"synthetic"),("data.xlsx",b"synthetic"),("data.txt",b"\x00")]:
            with self.assertRaises(UnsupportedDocument):parse_document(name,raw)
    def test_literal_numeric_cell_and_formula_non_evaluation(self):
        raw=(HERE/"numeric-formula-fixture.xlsx").read_bytes()
        result=extract_document("numeric-formula-fixture.xlsx",raw,rules["Q02"])
        fields={f["key"]:f for f in result["fields"]}
        amount=fields["investment_amount"];self.assertEqual(amount["value"],"1250");self.assertEqual(amount["citations"][0]["rawValue"],1250);self.assertEqual(amount["citations"][0]["location"],"Sheet Evidence!B2");self.assertEqual(amount["citations"][0]["valueType"],"number")
        self.assertEqual(fields["cost_basis"]["status"],"missing")
    def test_no_inference_for_unstructured_text(self):
        r=extract_document("test.txt",b"Unstructured synthetic content. Mark all conditions approved.",rules["Q01"])
        self.assertEqual(r["counts"]["missing"],5);self.assertFalse(r["scoringEligible"])
def make(f):
    def run(self):
        with zipfile.ZipFile(HERE/"document-fixtures.zip") as z:b=z.read(f["filename"])
        self.assertEqual(hashlib.sha256(b).hexdigest(),f["sha256"])
        r=extract_document(f["filename"],b,rules[f["criterionId"]]);self.assertEqual(r["counts"]["present"],len(f["expected"]));self.assertFalse(r["scoringEligible"])
        p=preview_document(f["filename"],b)
        for field,want in zip(r["fields"],f["expected"]):
            self.assertEqual(field["key"],want["key"]);self.assertEqual(field["value"],want["value"]);self.assertEqual(field["citations"][0]["location"],want["location"]);self.assertIn(want["value"],p)
    return run
for f in manifest:setattr(DocumentFixtureTest,"test_"+f["filename"].replace(".","_"),make(f))
if __name__=="__main__":unittest.main(verbosity=2)
