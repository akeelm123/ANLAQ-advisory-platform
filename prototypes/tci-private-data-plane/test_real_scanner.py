"""Opt-in harmless scanner check against installed official definitions."""
import os,unittest
import test_local_api as api
class RealScannerTests(unittest.TestCase):
 setUp=api.LocalAPITests.setUp
 tearDown=api.LocalAPITests.tearDown
 start=api.LocalAPITests.start
 stop=api.LocalAPITests.stop
 call=api.LocalAPITests.call
 post=api.LocalAPITests.post
 dash=api.LocalAPITests.dash
 upload=api.LocalAPITests.upload
 @unittest.skipUnless(os.getenv("TCI_TEST_REAL_SCANNER")=="1","Explicit installed scanner test opt-in")
 def test_harmless_strict_scan_and_restart(self):
    self.cfg["requireScan"]=True;self.start(True)
    self.assertEqual(self.dash("owner")[1]["intakeAssurance"]["scanner"],"ready_for_synthetic_scan")
    st,r=self.upload();self.assertEqual(st,201,r.get("error"));vid=r["record"]["versionId"]
    self.assertEqual(self.post("inspect","assessor",{"versionId":vid})[0],200)
    self.assertEqual(self.post("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Synthetic independently inspected format"})[0],200)
    self.start();data=self.dash("owner")[1]
    row=data["intakeAssurance"]["records"][0];self.assertEqual(row["scanStatus"],"clean");self.assertEqual(row["versionId"],vid);self.assertIn("ClamAV",row["scanMethod"])
    self.assertEqual(data["versions"][0]["status"],"accepted");self.assertEqual(self.post("release","owner",{})[0],403)
    print("PASS: actual installed ClamAV scan of harmless fictional document; version-bound clean record survived restart; release locked.")
if __name__=="__main__":unittest.main()
