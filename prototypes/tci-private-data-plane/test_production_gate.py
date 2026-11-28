import unittest
from production_gate import report
class ProductionGateTests(unittest.TestCase):
 def test_local_evidence_never_approves_production(self):
    r=report();self.assertEqual(r["operationalAccepted"],0);self.assertEqual(len(r["unacceptedGateIds"]),13);self.assertFalse(r["productionReady"]);self.assertTrue(r["releaseLocked"])
 def test_signed_private_attestation_evidence_binding(self):
    import tempfile,hashlib,json,base64
    from pathlib import Path
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    from production_gate import verify_private_attestations
    with tempfile.TemporaryDirectory() as d:
      p=Path(d)/"mock.txt";p.write_text("Mock evidence")
      key=Ed25519PrivateKey.generate();pub=key.public_key().public_bytes(serialization.Encoding.Raw,serialization.PublicFormat.Raw)
      record={"gateId":"P01","reviewerRef":"MOCK","requiredRole":"Project owner","target":"private-cloud","candidateCommit":"a"*40,"status":"accepted","reviewDate":"2026-11-28","dispositionRationale":"Mock test only","approvalReference":"Mock","evidence":[{"relativePath":"mock.txt","sha256":hashlib.sha256(p.read_bytes()).hexdigest()}]}
      signed={"record":record,"signature":base64.b64encode(key.sign(json.dumps(record,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode())).decode()}
      trust={"MOCK":{"roles":["Project owner"],"publicKey":base64.b64encode(pub).decode()}}
      r=verify_private_attestations([signed],trust,d,"private-cloud","a"*40)
      self.assertEqual(r["verifiedAttestationCount"],1);self.assertFalse(r["allSignedEvidencePresent"]);self.assertTrue(r["releaseLocked"])
      with self.assertRaises(ValueError):verify_private_attestations([signed],trust,d,"private-cloud","b"*40)
      p.write_text("Changed mock evidence")
      with self.assertRaises(ValueError):verify_private_attestations([signed],trust,d,"private-cloud","a"*40)
if __name__=="__main__":unittest.main()
