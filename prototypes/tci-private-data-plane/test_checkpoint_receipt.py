import secrets,tempfile,unittest,copy
from pathlib import Path
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from local_store import LocalStore,ROLES
from checkpoint_receipt import make_receipt,sign_receipt,verify_receipt,write_new
from data_plane import Invalid
import test_validation_workflow as base
class ReceiptTests(unittest.TestCase):
 def test_exact_checkpoint_and_rollback_guard(self):
    with tempfile.TemporaryDirectory() as tmp:
      p=Path(tmp);clock=lambda:1000000;accounts={r:(r,secrets.token_urlsafe(24)) for r in ROLES}
      with LocalStore(p/"vault",base.REGISTER,base.SPEC,clock=clock) as s:
        aid=s.initialize(secrets.token_urlsafe(24),accounts);old=s.current.read_bytes()
        token=s.dp.login(*accounts["assessor"]);s.dp.mark_request(token,aid,"SA-01","requested","Fictional");s.checkpoint();latest=s.current.read_bytes()
        r=make_receipt(latest,s.keys,base.REGISTER,base.SPEC,clock);k=Ed25519PrivateKey.generate();sig=sign_receipt(r,k)
        self.assertEqual(verify_receipt(sig,latest,k.public_key())["status"],"exact_signed_checkpoint_match")
        for blob,pub in ((old,k.public_key()),(latest,Ed25519PrivateKey.generate().public_key())):
          with self.assertRaises(Invalid):verify_receipt(sig,blob,pub)
        bad=copy.deepcopy(sig);bad["receipt"]["auditSeq"]+=1
        with self.assertRaises(Invalid):verify_receipt(bad,latest,k.public_key())
        f=p/"receipt.json";write_new(f,sig);self.assertEqual(f.stat().st_mode&0o777,0o600)
        with self.assertRaises(FileExistsError):write_new(f,sig)
if __name__=="__main__":unittest.main()
