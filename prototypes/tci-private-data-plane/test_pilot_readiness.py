import unittest
from pilot_readiness import report
class ReadinessTests(unittest.TestCase):
 def test_report_distinguishes_local_from_operational(self):
    r=report()
    self.assertEqual(r["requiredGates"],13);self.assertEqual(r["localVerified"],4)
    self.assertEqual(r["operationalAccepted"],0);self.assertEqual(r["pilotDeployment"],"blocked");self.assertEqual(r["production"],"locked")
if __name__=="__main__":unittest.main()
