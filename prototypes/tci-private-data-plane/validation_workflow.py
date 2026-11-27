"""Integrated evidence validation; structured human inputs and exact source checks, no scoring."""
from __future__ import annotations
import base64,json,secrets,uuid
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from document_parser import parse_document,UnsupportedDocument

METHOD="0.4.0-alpha.1"
def newid():return uuid.uuid4().hex
class ValidationWorkflow:
    def __init__(self,dp,invalid,denied,required):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.Denied=denied;self.required=required
        self.rules=dp.rules
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS validation_drafts(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),criterion TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),spec_hash TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS validation_reviews(id TEXT PRIMARY KEY,draft_id TEXT UNIQUE NOT NULL REFERENCES validation_drafts(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS validation_conflict_resolutions(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),conflict_id TEXT NOT NULL REFERENCES interview_conflicts(id),reviewer TEXT NOT NULL REFERENCES users(id),payload TEXT NOT NULL,created_at REAL NOT NULL);
        """)
        for table in ["validation_drafts","validation_reviews","validation_conflict_resolutions"]:
            self.db.executescript(f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'immutable validation record'); END; CREATE TRIGGER IF NOT EXISTS {table}_immutable_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'immutable validation record'); END;")
    def _seal(self,id,payload):
        nonce=secrets.token_bytes(12);ciphertext=AESGCM(self.dp.key).encrypt(nonce,json.dumps(payload,ensure_ascii=False,separators=(",",":")).encode(),id.encode())
        return base64.b64encode(nonce+ciphertext).decode()
    def _open(self,id,payload):
        raw=base64.b64decode(payload);return json.loads(AESGCM(self.dp.key).decrypt(raw[:12],raw[12:],id.encode()))
    def _actor(self,token,assessment,roles):return self.dp._actor(token,assessment,roles)
    def _ref(self,actor,assessment,criterion,ref):
        if not isinstance(ref,dict) or ref.get("requestId") not in self.dp.mappings[criterion]:raise self.Invalid("Approved evidence mapping required")
        locator=self.required(ref.get("locator"),"exact source locator");quote=self.required(ref.get("quote"),"exact source quote")
        v=self.dp._version(assessment,ref.get("versionId"))
        if v["status"]!="accepted" or not self.dp._latest(v):raise self.Invalid("Only accepted current source versions")
        intake=self.db.execute("SELECT request_id,source_owner,period,source_version FROM intake WHERE version_id=?",(v["id"],)).fetchone()
        if intake is None or intake["request_id"]!=ref["requestId"]:raise self.Invalid("Verified intake request linkage required")
        raw=self.dp._read_bytes(actor,assessment,v)
        try:segments=parse_document(v["filename"],raw)["segments"]
        except UnsupportedDocument as e:raise self.Invalid(str(e)) from e
        matches=[]
        for seg in segments:
            original=seg["pair"]["value"] if "pair" in seg else seg["text"]
            location=seg["pair"]["valueLocation"] if "pair" in seg else seg["location"]
            if location==locator and original.count(quote)==1:
                start=original.index(quote);matches.append({"versionId":v["id"],"requestId":ref["requestId"],"locator":locator,"quote":quote,"startColumn":start+1,"endColumn":start+len(quote),"sourceSha256":v["digest"],"sourceOwner":intake["source_owner"],"period":intake["period"],"sourceVersion":intake["source_version"],"contributorId":v["created_by"]})
        if len(matches)!=1:raise self.Invalid("Quote must match a unique exact span at the specified source location")
        return matches[0]
    def _refs_current(self,assessment,refs):
        return all(self.dp._latest(v) and v["status"]=="accepted" and v["digest"]==r["sourceSha256"] for r in refs for v in [self.dp._version(assessment,r["versionId"])])
    def _previewed(self,actor,assessment,refs):
        return all(self.db.execute("SELECT 1 FROM audit WHERE assessment_id=? AND actor=? AND action='evidence downloaded' AND record_id=?",(assessment,actor["id"],r["versionId"])).fetchone() for r in refs)
    def _conflicts(self,assessment,criterion):
        return list(self.db.execute("""SELECT f.* FROM interview_conflicts f JOIN interview_claims c ON c.id=f.claim_a JOIN interview_responses r ON r.id=c.response_id WHERE f.assessment_id=? AND r.question_id=? AND f.material=1""",(assessment,criterion)))
    def conflict_status(self,assessment,conflict):
        rec=self.db.execute("SELECT id FROM interview_conflicts WHERE id=? AND assessment_id=?",(conflict,assessment)).fetchone()
        if not rec:raise self.Denied("Access denied")
        rs=list(self.db.execute("SELECT * FROM validation_conflict_resolutions WHERE conflict_id=? AND assessment_id=? ORDER BY created_at DESC,rowid DESC",(conflict,assessment)))
        if not rs:return "open"
        last=rs[0];p=self._open(last["id"],last["payload"])
        return "resolved" if self._refs_current(assessment,p["refs"]) else "resolution superseded"
    def conflict_resolution(self,token,assessment,conflict,reason,refs,confirmed=False):
        if confirmed is not True:raise self.Invalid("Independent reconciliation confirmation required")
        reason=self.required(reason,"reconciliation rationale")
        if not isinstance(refs,list) or not 1<=len(refs)<=20:raise self.Invalid("Resolution evidence references required")
        with self.db:
            a=self._actor(token,assessment,{"reviewer"})
            f=self.db.execute("SELECT * FROM interview_conflicts WHERE id=? AND assessment_id=?",(conflict,assessment)).fetchone()
            if not f:raise self.Denied("Access denied")
            c1=self.dp.interviews._claim(assessment,f["claim_a"]);c2=self.dp.interviews._claim(assessment,f["claim_b"])
            if a["id"] in {f["author"],c1["author"],c2["author"]}:raise self.Denied("Independent reviewer required")
            if self.conflict_status(assessment,conflict)=="resolved":raise self.Invalid("Current resolution already exists")
            checked=[self._ref(a,assessment,c1["question_id"],r) for r in refs]
            if not self._previewed(a,assessment,checked):raise self.Invalid("Reviewer must preview each resolution source")
            rid=newid();self.db.execute("INSERT INTO validation_conflict_resolutions VALUES (?,?,?,?,?,?)",(rid,assessment,conflict,a["id"],self._seal(rid,{"reason":reason,"refs":checked,"confirmed":True}),self.dp.clock()))
            self.dp._audit(assessment,a["id"],"independent conflict resolution recorded",rid);return rid
    def draft(self,token,assessment,criterion,body):
        if criterion not in self.rules or not isinstance(body,dict):raise self.Invalid("Approved criterion required")
        if body.get("applicability") not in {"applicable","unknown","not_applicable"} or body.get("condition") not in {"met","not_met","unknown"} or body.get("evidenceClass") not in {"E1","E2","E3","E4"} or body.get("strength") not in {"Strong","Moderate","Weak","Not assessed"}:raise self.Invalid("Invalid validation classification")
        required_bools=["fieldsVerified","comparable","materialityReviewed","requiresCorroboration","documentaryConflict"]
        if any(type(body.get(k)) is not bool for k in required_bools):raise self.Invalid("Explicit structured assessor observations required")
        if body.get("conditionalApplies") not in (True,False,None) or (body.get("conditionalApplies") is not None and type(body["conditionalApplies"]) is not bool):raise self.Invalid("Conditional applicability invalid")
        refs=body.get("refs",[]);claims=body.get("claimIds",[])
        if not isinstance(refs,list) or len(refs)>20 or not isinstance(claims,list) or len(claims)>30 or len(set(claims))!=len(claims):raise self.Invalid("Invalid evidence or interview links")
        with self.db:
            a=self._actor(token,assessment,{"assessor"})
            checked=[self._ref(a,assessment,criterion,r) for r in refs]
            match_ids=body.get("matchIds",[])
            checked.extend(self.dp.matching.linked_refs(token,assessment,criterion,match_ids,claims))
            if len(checked)>20:raise self.Invalid("At most 20 exact evidence references per draft")
            for cid in claims:
                c=self.dp.interviews._claim(assessment,cid)
                if c["question_id"]!=criterion:raise self.Invalid("Interview claim must match criterion")
            def optional(k):
                x=body.get(k,"")
                if not isinstance(x,str) or len(x)>4000:raise self.Invalid(k+" invalid")
                return x.strip()
            payload={k:body[k] for k in ["applicability","condition","evidenceClass","strength",*required_bools]}
            payload.update({"claim":self.required(body.get("claim"),"draft finding"),"rationale":self.required(body.get("rationale"),"assessment rationale / limitations"),"owner":self.required(body.get("owner"),"finding / follow-up owner"),"followUp":optional("followUp"),"refs":checked,"claimIds":claims,"matchingCandidateIds":match_ids,"conditionalApplies":body.get("conditionalApplies"),"conditionalRationale":optional("conditionalRationale"),"alternativeRationale":optional("alternativeRationale"),"exceptionRationale":optional("exceptionRationale")})
            rid=newid();self.db.execute("INSERT INTO validation_drafts VALUES (?,?,?,?,?,?,?)",(rid,assessment,criterion,a["id"],self.dp.spec_hash,self._seal(rid,payload),self.dp.clock()))
            self.dp._audit(assessment,a["id"],"criterion validation draft created",rid);return rid
    def _draft_row(self,assessment,id):
        r=self.db.execute("SELECT * FROM validation_drafts WHERE id=? AND assessment_id=?",(id,assessment)).fetchone()
        if not r:raise self.Denied("Access denied")
        if r["spec_hash"]!=self.dp.spec_hash:raise self.Invalid("Validation specification mismatch")
        return r,self._open(r["id"],r["payload"])
    def _evaluate(self,assessment,criterion,p,review=None):
        rule=self.rules[criterion];refs=p["refs"];reasons=[]
        def out(state,reason):return {"state":state,"reason":reason,"scoringEligible":False}
        if p["applicability"]=="not_applicable":return out("exception_pending","Owner-approved exception and denominator rules outstanding")
        if p["applicability"]!="applicable":return out("insufficient","Applicability unresolved")
        conflicts=[f["id"] for f in self._conflicts(assessment,criterion) if self.conflict_status(assessment,f["id"])!="resolved"]
        if p["documentaryConflict"] or conflicts:return out("contradiction","Open material contradiction; preserve both accounts and reconcile with independent evidence")
        if not self._refs_current(assessment,refs):return out("superseded","A cited evidence version is no longer current")
        ids={r["requestId"] for r in refs}
        if not ids.intersection(rule["primary"]) and not (refs and p["alternativeRationale"]):return out("insufficient","Primary or documented mapped equivalent required")
        if rule["conditional"]:
            if p["conditionalApplies"] is None:return out("insufficient","Conditional applicability unresolved")
            if p["conditionalApplies"] and not set(rule["conditional"])<=ids:return out("insufficient","Applicable conditional evidence missing")
            if not p["conditionalApplies"] and not p["conditionalRationale"]:return out("insufficient","Out-of-scope rationale missing")
        if not p["fieldsVerified"] or not p["comparable"]:return out("insufficient","Required fields or comparable basis not verified")
        if p["evidenceClass"] not in {"E1","E2"} or p["strength"] in {"Not assessed","Weak"}:return out("insufficient","Interview assertion, unknown support or weak/unassessed strength")
        independent=p["requiresCorroboration"] or p["evidenceClass"]=="E2"
        if independent and (len({r["sourceSha256"] for r in refs})<2 or len({r["contributorId"] for r in refs})<2 or len({r["sourceOwner"].strip().casefold() for r in refs})<2):return out("insufficient","Distinct source documents, contributors and owners required; independence reviewed separately")
        if p["condition"]=="unknown" or not p["materialityReviewed"]:return out("insufficient","Condition or materiality not established")
        if not review:return out("review_pending","Independent review of field meaning, provenance, common basis and materiality required")
        if not review.get("confirmed"):return out("review_pending","Reviewer confirmation missing")
        if not ids.intersection(rule["primary"]) and not review.get("alternativeAccepted"):return out("review_pending","Mapped equivalent not accepted by reviewer")
        if rule["conditional"] and not review.get("applicabilityConfirmed"):return out("review_pending","Conditional applicability not confirmed")
        if independent and not review.get("independenceConfirmed"):return out("review_pending","Independent corroboration not confirmed")
        return out("supported_met" if p["condition"]=="met" else "supported_not_met","Independent human evidence review supports this condition; no score assigned")
    def review(self,token,assessment,id,decision,reason,controls):
        if decision not in {"accept","return"} or not isinstance(controls,dict):raise self.Invalid("Invalid validation review")
        with self.db:
            a=self._actor(token,assessment,{"reviewer"});row,p=self._draft_row(assessment,id)
            if row["author"]==a["id"]:raise self.Denied("Independent reviewer required")
            if self.db.execute("SELECT 1 FROM validation_reviews WHERE draft_id=?",(id,)).fetchone():raise self.Invalid("Validation already reviewed; draft a revision")
            flags={k:controls.get(k) is True for k in ["confirmed","alternativeAccepted","applicabilityConfirmed","independenceConfirmed"]}
            if decision=="accept":
                result=self._evaluate(assessment,row["criterion"],p,flags)
                if result["state"] not in {"supported_met","supported_not_met"}:raise self.Invalid(result["reason"])
                if not self._previewed(a,assessment,p["refs"]):raise self.Invalid("Reviewer must preview every linked source")
            else:result=self._evaluate(assessment,row["criterion"],p)
            review_id=newid();self.db.execute("INSERT INTO validation_reviews VALUES (?,?,?,?,?,?)",(review_id,id,a["id"],decision,self._seal(review_id,{"reason":self.required(reason,"independent review rationale"),"controls":flags,"decisionState":result["state"]}),self.dp.clock()))
            self.dp._audit(assessment,a["id"],"criterion validation review "+decision,review_id);return review_id
    def view(self,token,assessment):
        self._actor(token,assessment,{"assessor","reviewer","owner"})
        data=[]
        for row in self.db.execute("SELECT * FROM validation_drafts WHERE assessment_id=? ORDER BY created_at,rowid",(assessment,)):
            p=self._open(row["id"],row["payload"]);rev=self.db.execute("SELECT * FROM validation_reviews WHERE draft_id=?",(row["id"],)).fetchone()
            review=self._open(rev["id"],rev["payload"]) if rev else None
            state=self._evaluate(assessment,row["criterion"],p,review["controls"] if rev and rev["decision"]=="accept" else None)
            if rev and rev["decision"]=="return":state={**state,"state":"returned","reason":review["reason"]}
            data.append({"id":row["id"],"criterion":row["criterion"],"payload":p,"state":state,"review":{**review,"decision":rev["decision"]} if rev else None,"scoringEligible":False})
        conflicts=[]
        for f in self.db.execute("SELECT * FROM interview_conflicts WHERE assessment_id=? ORDER BY created_at",(assessment,)):
            c=self.dp.interviews._claim(assessment,f["claim_a"]);rs=list(self.db.execute("SELECT * FROM validation_conflict_resolutions WHERE conflict_id=? ORDER BY created_at,rowid",(f["id"],)))
            conflicts.append({"id":f["id"],"criterion":c["question_id"],"status":self.conflict_status(assessment,f["id"]),"material":bool(f["material"]),"resolutions":[self._open(r["id"],r["payload"]) for r in rs]})
        return {"method":METHOD,"rules":list(self.rules.values()),"drafts":data,"conflicts":conflicts,"scoringEligible":False}
