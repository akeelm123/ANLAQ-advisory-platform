"""Defensive synthetic scanner-policy and bounded child parser tests."""
import json,secrets,tempfile,unittest,zipfile,subprocess
from pathlib import Path
from unittest.mock import patch
from data_plane import DataPlane,Invalid,Denied
from document_parser import enable_child_parser,parse_document,UnsupportedDocument
import test_validation_workflow as base

class IntakeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
    cls.dp=DataPlane(":memory:",secrets.token_bytes(32),secrets.token_bytes(32),base.REGISTER,base.SPEC);cls.tokens={};cls.ids={}
    for n in ["assessor","reviewer","owner","contributor","contributor2","other"]:
      pw=secrets.token_urlsafe(24);u=cls.dp.bootstrap_user(n,pw);cls.ids[n]=u;cls.tokens[n]=cls.dp.login(n,pw)
 @classmethod
 def tearDownClass(cls):cls.dp.close()
 def setUp(self):
    base.ValidationTests.setUp(self);self.dp.intake_assurance.require_scan=False
 def tearDown(self):self.dp.intake_assurance.require_scan=False;enable_child_parser(False)
 t=base.ValidationTests.t
 def upload(self,text=b"Fictional test evidence"):
    return self.dp.upload(self.t("contributor"),self.a,"Fictional source","test.txt",text,intake={"criterion":"Q01","requestId":"SA-01","sourceOwner":"Mock owner","period":"Mock","sourceVersion":"1","locator":"Text line 1"})
 def view(self):return self.dp.intake_assurance.view(self.t("owner"),self.a)
 def test_default_not_scanned_never_clean(self):
    self.upload();r=self.view()["records"][0];self.assertEqual(r["scanStatus"],"not_scanned");self.assertEqual(r["outcome"],"quarantined")
    with self.assertRaises(Denied):self.dp.intake_assurance.view(self.t("contributor"),self.a)
 def test_strict_scan_mock_outcomes_fail_closed(self):
    self.dp.intake_assurance.require_scan=True
    for state in ("unavailable","detected","not_scanned"):
      with patch("intake_assurance.scan_installed",return_value={"status":state,"method":"Mock scanner response"}):
        with self.assertRaises(Invalid):self.upload()
    self.assertEqual(len(self.dp.list_versions(self.t("owner"),self.a)),0)
    self.assertTrue(all(r["outcome"]=="refused" and r["versionId"] is None for r in self.view()["records"]))
    with patch("intake_assurance.scan_installed",return_value={"status":"clean","method":"Mock clean scan"}):
      v=self.upload()
    self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"]);self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Mock independent screen")
    self.assertEqual(self.view()["records"][-1]["scanStatus"],"clean")
 def test_strict_cannot_accept_old_unscanned_quarantine(self):
    v=self.upload();self.dp.intake_assurance.require_scan=True
    self.dp.inspect_quarantine(self.t("assessor"),self.a,v["versionId"])
    with self.assertRaises(Invalid):self.dp.screen(self.t("assessor"),self.a,v["versionId"],"accepted","Mock")
 def test_parser_refusal_records_digest_only(self):
    enable_child_parser()
    with self.assertRaises(Invalid):self.upload(b"Fictional unsupported control \x00")
    r=self.view()["records"][0];self.assertEqual(r["outcome"],"refused");self.assertEqual(r["parserMode"],"bounded_child_process");self.assertIsNone(r["versionId"]);self.assertNotIn("Fictional unsupported",str(r));self.assertTrue(self.dp.verify_audit())
 def test_child_parser_four_formats_preserves_exact_locations(self):
    root=Path(__file__).resolve().parent
    fixtures=json.loads((root/"golden-document-fixtures.json").read_text())["fixtures"]
    cases=[("mock.txt",b"Synthetic first line\nSecond line")]
    with zipfile.ZipFile(root/"document-fixtures.zip") as z:
      for ext in ("pdf","docx","xlsx"):
        f=next(f for f in fixtures if f["filename"].endswith(ext));cases.append((f["filename"],z.read(f["filename"])))
    for name,raw in cases:
      enable_child_parser(False);expected=parse_document(name,raw);enable_child_parser();self.assertEqual(parse_document(name,raw),expected)
 def test_child_timeout_fail_closed(self):
    enable_child_parser()
    with patch("document_parser.subprocess.run",side_effect=subprocess.TimeoutExpired("synthetic child",15)):
      with self.assertRaises(UnsupportedDocument):parse_document("test.txt",b"Fictional")
 def test_scanner_adapter_not_installed(self):
    from intake_assurance import scan_installed
    with patch("intake_assurance.scanner_command",return_value=None):self.assertEqual(scan_installed(b"Fictional")["status"],"unavailable")
 def test_signature_freshness_candidate_policy(self):
    from datetime import date
    from intake_assurance import signature_age,scan_installed
    self.assertEqual(signature_age("ClamAV 1.5.4/28194/Wed Nov 25 14:26:59 2026",date(2026,11,28)),3)
    self.assertIsNone(signature_age("ClamAV 1.5.4/28194/Wed Nov 25 14:26:59 2026",date(2026,12,5)))
    self.assertIsNone(signature_age("ClamAV 1.5.4"))
    with patch("intake_assurance.scanner_command",return_value=["mock-scanner"]),patch("intake_assurance._version",return_value="ClamAV 1.5.4"),patch("intake_assurance.subprocess.run") as run:
      self.assertEqual(scan_installed(b"Fictional")["status"],"unavailable");run.assert_not_called()
if __name__=="__main__":unittest.main()
