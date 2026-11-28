"""Scripted synthetic lifecycle rehearsal via persistent loopback API and new-vault recovery."""
import base64,json,unittest,os
from pathlib import Path
import test_local_api as api
from local_store import LocalStore
from serve import REGISTER,SPEC

class LocalLifecycleUAT(unittest.TestCase):
    setUp=api.LocalAPITests.setUp
    tearDown=api.LocalAPITests.tearDown
    start=api.LocalAPITests.start
    stop=api.LocalAPITests.stop
    call=api.LocalAPITests.call
    post=api.LocalAPITests.post
    dash=api.LocalAPITests.dash
    def ok(self,action,role,data,status=201):
        st,r=self.post(action,role,data);self.assertEqual(st,status,f"{action}: {r.get('error','unexpected status')}");return r
    def upload_extract(self,f,document=None,suffix=""):
        q=f["criterionId"];req=f["requestId"]
        v=self.ok("upload","contributor",{"title":"MOCK UAT "+q,"filename":q+".txt","documentId":document,"contentBase64":base64.b64encode((f["text"]+suffix).encode()).decode(),"intake":{"criterion":q,"requestId":req,"sourceOwner":"Fictional UAT owner","period":"Mock review periods","sourceVersion":"2" if document else "1","locator":"Text fixture"}})["record"]
        vid=v["versionId"];self.ok("inspect","assessor",{"versionId":vid},200);self.ok("screen","assessor",{"versionId":vid,"decision":"accepted","reason":"Scripted fictional format screening"},200)
        run=self.ok("extract","assessor",{"versionId":vid,"criterion":q})["runId"]
        self.ok("preview","reviewer",{"versionId":vid},200);d=self.dash("reviewer")[1]
        result=next(x["result"] for x in d["extractions"] if x["id"]==run)
        self.assertEqual(result["counts"]["present"],len(f["expected"]));self.assertEqual(result["counts"]["missing"]+result["counts"]["ambiguous"],0)
        for field in f["expected"]:self.assertEqual(next(x["value"] for x in result["fields"] if x["key"]==field["key"]),field["value"])
        self.ok("extraction-review","reviewer",{"runId":run,"decision":"accept","reason":"Scripted source-field check","confirmed":True},200)
        refs=[{"versionId":vid,"requestId":req,"locator":"Text line "+str(e["line"]),"quote":e["excerpt"]} for e in f["expected"]]
        return v,refs
    def claim(self,q,persona,ref,text):
        sid=self.ok("interview-start","assessor",{"persona":persona,"stakeholderRef":ref,"role":"Fictional stakeholder","scope":"Mock UAT"})["sessionId"]
        return self.ok("interview-response","assessor",{"sessionId":sid,"questionId":q,"status":"answered","verbatim":text,"interpretation":"Scripted fictional claim","flags":[],"links":[]})["claimId"]
    def matching(self,q,cid,ref):
        rid=self.ok("matching-propose","assessor",{"criterion":q,"claimId":cid,"query":ref["quote"],"mode":"ranked"})["runId"]
        r=next(x for x in self.dash("assessor")[1]["matching"]["runs"] if x["id"]==rid)
        m=next((c for c in r["candidates"] if c["versionId"]==ref["versionId"] and c["quote"]==ref["quote"]),None)
        self.assertIsNotNone(m,"Expected exact primary passage retrieved")
        self.ok("preview","assessor",{"versionId":ref["versionId"]},200)
        self.ok("matching-review","assessor",{"runId":rid,"candidateId":m["id"],"decision":"link","reason":"Scripted relevance check only","confirmed":True})
        return m["id"]
    def validate(self,q,refs,claim_ids=(),matches=(),adverse=False):
        body={"criterion":q,"applicability":"applicable","condition":"not_met" if adverse else "met","evidenceClass":"E1","strength":"Strong","fieldsVerified":True,"comparable":True,"materialityReviewed":True,"requiresCorroboration":False,"documentaryConflict":False,"claim":"MOCK scripted criterion condition","rationale":"Structural UAT; not semantic judgement or actual performance","owner":"Fictional UAT owner","followUp":"Mock follow-up","conditionalApplies":False,"conditionalRationale":"Mock AI out of scope","refs":refs,"claimIds":list(claim_ids),"matchIds":list(matches)}
        did=self.ok("validation-draft","assessor",body)["draftId"]
        self.ok("validation-review","reviewer",{"draftId":did,"decision":"accept","reason":"Scripted independent mock review","controls":{"confirmed":True,"applicabilityConfirmed":True}})
        return did
    def snap(self,label,start,end):
        sid=self.ok("reassessment-capture","assessor",{"label":label,"periodStart":start,"periodEnd":end,"basis":"Identical mock population and measurement basis"})["snapshotId"]
        self.ok("reassessment-snapshot-review","reviewer",{"snapshotId":sid,"decision":"accept","reason":"Scripted period review","confirmed":True});return sid
    def test_complete_persistent_lifecycle_and_recovery(self):
        strict=os.getenv("TCI_TEST_STRICT_FULL_UAT")=="1"
        if strict:self.cfg["requireScan"]=True
        self.start(True)
        fixtures=json.loads((Path(__file__).resolve().parent/"golden-fixtures.json").read_text())["fixtures"]
        docs={};refs={};validations=[];match_count=0
        for f in fixtures:
            q=f["criterionId"];docs[q],refs[q]=self.upload_extract(f)
        # Representative interviews and matching across all seven dimensions; 28 document checks.
        for q in ("Q01","Q05","Q09","Q13","Q17","Q21","Q25"):
            c=self.claim(q,"Mock assessor exercise "+q,"MOCK-"+q,refs[q][0]["quote"])
            mid=self.matching(q,c,refs[q][0]);match_count+=1
            if q=="Q25":
                c2=self.claim(q,"Mock conflicting persona","MOCK-Q25-2","Fictional competing benefits assertion")
                conflict=self.ok("interview-conflict","assessor",{"claimA":c,"claimB":c2,"topic":"Mock material benefit disagreement","material":True})["conflictId"]
                self.ok("validation-conflict-resolution","reviewer",{"conflictId":conflict,"reason":"Scripted mock reconciliation; no actual financial evidence","refs":refs[q],"confirmed":True})
                claims=[c,c2]
            else:claims=[c]
            validations.append(self.validate(q,refs[q][1:],claims,[mid],adverse=q in ("Q13","Q25")))
        remaining={f["criterionId"] for f in fixtures}-{ "Q01","Q05","Q09","Q13","Q17","Q21","Q25"}
        for q in sorted(remaining):validations.append(self.validate(q,refs[q]))
        self.assertEqual(match_count,7);self.assertEqual(len(validations),28)
        d=self.dash("owner")[1];self.assertEqual(d["executive"]["snapshot"]["supportedCount"],28);self.assertFalse(d["pilotScoring"]["enabled"])
        b=self.ok("executive-draft","assessor",{"title":"MOCK complete UAT brief","summary":"Scripted verified workflow, not actual assessment","limitations":"All evidence and outcomes are fictional control fixtures","findingIds":validations,"options":[{"direction":"Correct","rationale":"Scripted condition","consequences":"Mock resource implications"},{"direction":"Reassess","rationale":"Mock alternative","consequences":"Mock delay"}],"actions":[{"condition":"Mock benefits condition","owner":"Mock accountable owner","followUp":"Review revised mock source"}]})["briefId"]
        self.ok("executive-review","reviewer",{"briefId":b,"decision":"accept","reason":"Scripted brief review","confirmed":True})
        self.ok("executive-direction","owner",{"briefId":b,"direction":"Correct","reason":"Scripted owner choice","conditions":"Mock conditions only","confirmed":True})
        baseline=self.snap("Mock baseline","2026-01-01","2026-03-31")
        # Restart the encrypted server before follow-up.
        old=self.tokens["owner"];self.start();self.assertEqual(self.call("/api/assessments",token=old)[0],403)
        d=self.dash("owner")[1];self.assertEqual(d["executive"]["snapshot"]["supportedCount"],28);self.assertEqual(len(d["matching"]["runs"]),7)
        f=next(f for f in fixtures if f["criterionId"]=="Q25");_,newrefs=self.upload_extract(f,docs["Q25"]["documentId"],"\nMOCK follow-up revision; not real assessment\n")
        self.assertEqual(self.dash("owner")[1]["executive"]["snapshot"]["supportedCount"],27)
        self.ok("validation-conflict-resolution","reviewer",{"conflictId":conflict,"reason":"Scripted revised mock reconciliation","refs":newrefs,"confirmed":True})
        new=self.validate("Q25",newrefs,[c,c2])
        follow=self.snap("Mock follow-up","2026-04-01","2026-06-30")
        snap=next(s for s in self.dash("owner")[1]["reassessment"]["snapshots"] if s["id"]==baseline)
        action=snap["payload"]["state"]["executive"]["actions"][0]
        comp=self.ok("reassessment-compare","assessor",{"baselineId":baseline,"followUpId":follow,"rationale":"Comparable mock periods only","confirmed":True,"actions":[{"actionId":action["id"],"status":"closed","rationale":"Scripted source-backed closure","findingIds":[new]}]})["comparisonId"]
        self.ok("reassessment-comparison-review","reviewer",{"comparisonId":comp,"decision":"accept","reason":"Scripted independent comparison","confirmed":True})
        self.assertEqual(self.post("release","owner",{})[0],403)
        self.stop()
        # Exercise offline archive and recovery to new vault; no user store touched.
        original=Path(self.cfg["directory"]);backup=Path(self.tmp.name)/"mock-backup.tci";newpath=Path(self.tmp.name)/"recovered"
        with LocalStore(original,REGISTER,SPEC) as store:
            store.unlock(self.cfg["passphrase"]);self.assertTrue(store.dp.verify_audit());store.backup(backup)
        with LocalStore(newpath,REGISTER,SPEC) as store:store.recover_backup(backup,original/"salt.bin",self.cfg["passphrase"]);self.assertTrue(store.dp.verify_audit())
        self.cfg["directory"]=str(newpath);self.start()
        d=self.dash("owner")[1];self.assertEqual(d["executive"]["snapshot"]["supportedCount"],28)
        self.assertEqual(len(d["versions"]),29);self.assertEqual(len(d["matching"]["runs"]),7)
        if strict:self.assertEqual(sum(r["scanStatus"]=="clean" for r in d["intakeAssurance"]["records"]),29)
        c=next(c for c in d["reassessment"]["comparisons"] if c["id"]==comp);self.assertEqual(c["status"],"accept")
        self.assertEqual(next(x for x in c["payload"]["result"]["criteria"] if x["criterion"]=="Q25")["change"],"condition_improved")
        self.assertEqual(c["payload"]["actions"][0]["status"],"closed");self.assertIsNone(c["payload"]["result"]["pilot"])
        self.assertIsNone(self.dash("contributor")[1]["matching"]);self.assertEqual(self.post("release","owner",{})[0],403)
        print("PASS: 28 criteria and exact source extraction, seven claim-linked matches, material conflict reconciliation, 28 reviewed findings, two accepted periods, source supersession, reviewed action closure, restart, new-vault encrypted recovery; persistent scoring disabled.")
if __name__=="__main__":unittest.main()
