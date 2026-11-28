import unittest
from simple_ai import verify
class ModelCandidateTests(unittest.TestCase):
    def setUp(self):
        self.items=[{"id":"Q01","sources":[{"id":"1"}]}]
    def test_valid_reference_and_unknown(self):
        for score,refs in [(3,["1"]),(None,[])]:
            v=verify(self.items,{"results":[{"id":"Q01","score":score,"sourceIds":refs,"rationale":"Fictional review candidate"}]})
            self.assertEqual(v["Q01"]["score"],score)
    def test_reject_fabricated_reference_and_non_integer(self):
        for score,refs in [(3,["2"]),(True,["1"]),(5,[])]:
            with self.assertRaises(ValueError):verify(self.items,{"results":[{"id":"Q01","score":score,"sourceIds":refs,"rationale":"Mock"}]})
