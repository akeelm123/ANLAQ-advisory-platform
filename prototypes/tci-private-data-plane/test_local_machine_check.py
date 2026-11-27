import unittest
from unittest.mock import patch
from local_machine_check import filevault_status,check
class MachineCheckTests(unittest.TestCase):
 def test_filevault_states_fail_closed(self):
    self.assertEqual(filevault_status("FileVault is Off."),"off")
    self.assertEqual(filevault_status("FileVault is On."),"on")
    for x in (None,"","Unrecognised"):self.assertEqual(filevault_status(x),"unverified")
 def test_never_infers_operational_approval(self):
    with patch("local_machine_check.command",side_effect=["25769803776","FileVault is On.","synthetic OS"]):
      r=check();self.assertEqual(r["machineEncryptionGate"],"requires_independent_verification");self.assertFalse(r["operationalAccepted"]);self.assertFalse(r["realClientAuthorised"])
if __name__=="__main__":unittest.main()
