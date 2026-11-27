"""Verify proposed design declarations only; no live infrastructure tests."""
import copy,json,unittest
from pilot_architecture import HERE,verify_design
class ArchitectureTests(unittest.TestCase):
 def setUp(self):self.d=json.loads((HERE/"PRIVATE-PILOT-ARCHITECTURE.json").read_text())
 def test_locked_proposed_design_and_budget(self):
    x=verify_design(self.d);self.assertEqual(x["deployment"],"blocked");self.assertEqual(x["operationalGatesAccepted"],0);self.assertEqual(x["monthlyPlanningUsd"],{"low":450,"high":900})
 def test_public_network_and_external_model_disallowed(self):
    for key in ("applicationPublicIngress","applicationPublicIp","databasePublicAccess","externalModelEgress"):
      with self.subTest(key=key):
        d=copy.deepcopy(self.d);d["network"][key]=True
        with self.assertRaises(ValueError):verify_design(d)
 def test_required_identity_controls(self):
    for key in ("mfaRequired","serverSideMembership","distinctReviewer","sessionRevocation"):
      d=copy.deepcopy(self.d);d["identity"][key]=False
      with self.assertRaises(ValueError):verify_design(d)
 def test_required_storage_and_intake_controls(self):
    for key in ("customerManagedKeys","separateKeyPurposes","managedSecretStore","scannerIsolation","failClosedIntake","externalAudit"):
      d=copy.deepcopy(self.d);d["data"][key]=False
      with self.assertRaises(ValueError):verify_design(d)
 def test_no_inferred_authority(self):
    for key in self.d["authority"]:
      d=copy.deepcopy(self.d);d["authority"][key]=True
      with self.assertRaises(ValueError):verify_design(d)
 def test_region_and_cohort_limits(self):
    for key,val in (("dataRegion","us-east-1"),("cohortLimit",100),("inputClass","real-client")):
      d=copy.deepcopy(self.d);d["scope"][key]=val
      with self.assertRaises(ValueError):verify_design(d)
 def test_local_architecture_loopback_only(self):
    x=verify_design(self.d);self.assertEqual(x["localOption"]["deployment"],"blocked");self.assertEqual(x["localOption"]["monthlyIncrementalPlanningUsd"],{"low":0,"high":40})
    for key in ("lanAccess","publicIngress","remoteAccess","externalModelEgress","cloudSync"):
      d=copy.deepcopy(self.d);d["localOption"]["network"][key]=True
      with self.assertRaises(ValueError):verify_design(d)
    d=copy.deepcopy(self.d);d["localOption"]["network"]["bindAddress"]="0.0.0.0"
    with self.assertRaises(ValueError):verify_design(d)
 def test_local_architecture_encrypted_storage_and_roles(self):
    for key in ("encryptedVolumeRequired","separateArchiveKeysRequired","encryptedOfflineBackup"):
      d=copy.deepcopy(self.d);d["localOption"]["data"][key]=False
      with self.assertRaises(ValueError):verify_design(d)
    d=copy.deepcopy(self.d);d["localOption"]["identity"]["sharedCredentials"]=True
    with self.assertRaises(ValueError):verify_design(d)
if __name__=="__main__":unittest.main()
