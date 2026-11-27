"""Authenticated synthetic stakeholder interview workflow; no autonomous contact or scoring."""
from __future__ import annotations
import hashlib,json,os,uuid,base64,secrets
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from interview_ai import propose as propose_wording
from narrative import NarrativeUnavailable
from pathlib import Path

SPEC_HASH="0c021f60d9e44beeaa19331abf02a2b080175aa07b4c6e68a45138640efbc9e9"
FLAGS={"incomparable_basis","forecast_vs_actual","conditional_unclear","vague_claim","assertion_only"}
METHOD="0.3.0-alpha.1"
def newid():return uuid.uuid4().hex

class InterviewWorkflow:
    def __init__(self,dp,invalid,denied,required):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.Denied=denied;self.required=required
        root=Path(__file__).resolve().parent.parent.parent
        path=Path(os.environ.get("TCI_INTERVIEW_SPEC",root/"docs/tci/interviews-v0.3-preparation/INTERVIEW-SPEC-v0.3-preparation.json"))
        raw=path.read_bytes()
        if hashlib.sha256(raw).hexdigest()!=SPEC_HASH:raise invalid("Interview specification hash mismatch")
        spec=json.loads(raw)
        if spec["registerSha256"]!=dp.register_hash or spec["validationSpecSha256"]!=dp.spec_hash:raise invalid("Interview methodology mismatch")
        self.cards={x["questionId"]:x for x in spec["cards"]};self.triggers={x["id"]:x for x in spec["followUpTriggers"]}
        if len(self.cards)!=28 or len(self.triggers)!=10:raise invalid("Interview spec count mismatch")
        for c in self.cards.values():
            if set(c["primaryRequests"]+c["supplementaryRequests"]+c["conditionalRequests"])!=dp.mappings[c["criterionId"]]:raise invalid("Interview mapping mismatch")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS interview_sessions(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),persona TEXT NOT NULL,stakeholder_ref TEXT NOT NULL,role TEXT NOT NULL,scope TEXT NOT NULL,creator TEXT NOT NULL REFERENCES users(id),spec_hash TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_responses(id TEXT PRIMARY KEY,session_id TEXT NOT NULL REFERENCES interview_sessions(id),question_id TEXT NOT NULL,question_text TEXT NOT NULL,status TEXT NOT NULL,verbatim TEXT NOT NULL,recorder TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_claims(id TEXT PRIMARY KEY,response_id TEXT UNIQUE NOT NULL REFERENCES interview_responses(id),interpretation TEXT NOT NULL,flags TEXT NOT NULL,claim_class TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_links(claim_id TEXT NOT NULL REFERENCES interview_claims(id),version_id TEXT NOT NULL REFERENCES versions(id),request_id TEXT NOT NULL,locator TEXT NOT NULL,PRIMARY KEY(claim_id,version_id,request_id));
        CREATE TABLE IF NOT EXISTS interview_conflicts(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),claim_a TEXT NOT NULL REFERENCES interview_claims(id),claim_b TEXT NOT NULL REFERENCES interview_claims(id),topic TEXT NOT NULL,material INTEGER NOT NULL,author TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_followups(id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES interview_claims(id),trigger_id TEXT NOT NULL,question TEXT NOT NULL,reason TEXT NOT NULL,request_ids TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_followup_answers(id TEXT PRIMARY KEY,followup_id TEXT UNIQUE NOT NULL REFERENCES interview_followups(id),verbatim TEXT NOT NULL,status TEXT NOT NULL,recorder TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_model_proposals(id TEXT PRIMARY KEY,claim_id TEXT NOT NULL REFERENCES interview_claims(id),trigger_id TEXT NOT NULL,model TEXT NOT NULL,model_digest TEXT NOT NULL,payload TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS interview_proposal_links(followup_id TEXT PRIMARY KEY REFERENCES interview_followups(id),proposal_id TEXT NOT NULL REFERENCES interview_model_proposals(id));
        CREATE TABLE IF NOT EXISTS interview_capture_reviews(id TEXT PRIMARY KEY,claim_id TEXT UNIQUE NOT NULL REFERENCES interview_claims(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,reason TEXT NOT NULL,created_at REAL NOT NULL);
        """)
        for table in ["interview_sessions","interview_responses","interview_claims","interview_links","interview_conflicts","interview_followups","interview_followup_answers","interview_capture_reviews","interview_model_proposals","interview_proposal_links"]:
            # Table identifiers are fixed internal constants, never user input.
            self.db.executescript(f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'immutable interview record'); END; CREATE TRIGGER IF NOT EXISTS {table}_immutable_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'immutable interview record'); END;")
    def _encrypt(self,record,field,text):
        nonce=secrets.token_bytes(12)
        ciphertext=AESGCM(self.dp.key).encrypt(nonce,text.encode(),json.dumps([record,field],separators=(",",":")).encode())
        return base64.b64encode(nonce+ciphertext).decode()
    def _decrypt(self,record,field,stored):
        raw=base64.b64decode(stored)
        return AESGCM(self.dp.key).decrypt(raw[:12],raw[12:],json.dumps([record,field],separators=(",",":")).encode()).decode()
    def _actor(self,token,assessment,roles):return self.dp._actor(token,assessment,roles)
    def _session(self,assessment,session):
        s=self.db.execute("SELECT * FROM interview_sessions WHERE id=? AND assessment_id=?",(session,assessment)).fetchone()
        if not s:raise self.Denied("Access denied")
        return s
    def _claim(self,assessment,claim):
        r=self.db.execute("""SELECT c.*,r.question_id,r.status AS response_status,r.verbatim,s.id AS session_id,s.persona,s.stakeholder_ref,s.role FROM interview_claims c JOIN interview_responses r ON r.id=c.response_id JOIN interview_sessions s ON s.id=r.session_id WHERE c.id=? AND s.assessment_id=?""",(claim,assessment)).fetchone()
        if not r:raise self.Denied("Access denied")
        return r
    def start(self,token,assessment,persona,stakeholder_ref,role,scope):
        with self.db:
            a=self._actor(token,assessment,{"assessor"})
            sid=newid();values=[self.required(x,k) for x,k in [(persona,"persona"),(stakeholder_ref,"synthetic stakeholder reference"),(role,"role"),(scope,"interview scope")]]
            self.db.execute("INSERT INTO interview_sessions VALUES (?,?,?,?,?,?,?,?,?)",(sid,assessment,*values,a["id"],SPEC_HASH,self.dp.clock()))
            self.dp._audit(assessment,a["id"],"interview session started",sid)
            return sid
    def record(self,token,assessment,session,question,status,verbatim,interpretation,flags,links):
        if question not in self.cards or status not in {"answered","unknown","declined"}:raise self.Invalid("Invalid approved question or response status")
        if not isinstance(flags,list) or not all(isinstance(x,str) and x in FLAGS for x in flags):raise self.Invalid("Invalid structured gap flags")
        if not isinstance(links,list):raise self.Invalid("Evidence link list required")
        if status=="answered":self.required(verbatim,"verbatim response")
        elif not isinstance(verbatim,str):raise self.Invalid("Response text invalid")
        elif len(verbatim)>4000:raise self.Invalid("Response length limit")
        interpretation=self.required(interpretation,"separate assessor interpretation / uncertainty")
        with self.db:
            a=self._actor(token,assessment,{"assessor"});self._session(assessment,session)
            card=self.cards[question];rid,cid=newid(),newid();cls="E3" if status=="answered" else "E4"
            self.db.execute("INSERT INTO interview_responses VALUES (?,?,?,?,?,?,?,?)",(rid,session,question,card["question"],status,self._encrypt(rid,"verbatim",verbatim),a["id"],self.dp.clock()))
            self.db.execute("INSERT INTO interview_claims VALUES (?,?,?,?,?,?,?)",(cid,rid,self._encrypt(cid,"interpretation",interpretation),json.dumps(sorted(set(flags))),cls,a["id"],self.dp.clock()))
            for link in links:
                if link["requestId"] not in self.dp.mappings[card["criterionId"]]:raise self.Invalid("Unmapped interview evidence")
                v=self.dp._version(assessment,link["versionId"])
                if v["status"]!="accepted" or not self.dp._latest(v):raise self.Invalid("Only accepted current evidence versions")
                intake=self.db.execute("SELECT request_id FROM intake WHERE version_id=?",(v["id"],)).fetchone()
                if intake and intake["request_id"]!=link["requestId"]:raise self.Invalid("Evidence request differs from intake")
                self.db.execute("INSERT INTO interview_links VALUES (?,?,?,?)",(cid,v["id"],link["requestId"],self.required(link["locator"],"precise locator")))
            self.dp._audit(assessment,a["id"],"interview response and draft claim recorded",cid)
            return cid
    def conflict(self,token,assessment,one,two,topic,material):
        if one==two or type(material) is not bool:raise self.Invalid("Distinct claims and materiality required")
        with self.db:
            a=self._actor(token,assessment,{"assessor"});x=self._claim(assessment,one);y=self._claim(assessment,two)
            if x["question_id"]!=y["question_id"] or x["session_id"]==y["session_id"] or x["stakeholder_ref"].strip().casefold()==y["stakeholder_ref"].strip().casefold():raise self.Invalid("Separate stakeholder claims for the same criterion required")
            key=tuple(sorted([one,two]))
            if self.db.execute("SELECT 1 FROM interview_conflicts WHERE assessment_id=? AND claim_a=? AND claim_b=?",(assessment,*key)).fetchone():raise self.Invalid("Conflict already recorded")
            id=newid();self.db.execute("INSERT INTO interview_conflicts VALUES (?,?,?,?,?,?,?,?)",(id,assessment,*key,self._encrypt(id,"topic",self.required(topic,"conflict topic")),int(material),a["id"],self.dp.clock()))
            self.dp._audit(assessment,a["id"],"interview contradiction recorded",id);return id
    def _linked(self,claim,assessment):
        links=[]
        for l in self.db.execute("SELECT version_id AS versionId,request_id AS requestId,locator FROM interview_links WHERE claim_id=?",(claim,)):
            v=self.dp._version(assessment,l["versionId"]);links.append({**dict(l),"current":self.dp._latest(v) and v["status"]=="accepted"})
        return links
    def suggest(self,token,assessment,claim):
        self._actor(token,assessment,{"assessor","reviewer","owner"});c=self._claim(assessment,claim);card=self.cards[c["question_id"]]
        flags=set(json.loads(c["flags"]));links=self._linked(claim,assessment)
        current={l["requestId"] for l in links if l["current"]};missing=not any(x in current for x in card["primaryRequests"])
        material=any(self.dp.validation.conflict_status(assessment,r["id"])!="resolved" for r in self.db.execute("SELECT id FROM interview_conflicts WHERE assessment_id=? AND material=1 AND (claim_a=? OR claim_b=?)",(assessment,claim,claim)))
        review=self.db.execute("SELECT decision FROM interview_capture_reviews WHERE claim_id=?",(claim,)).fetchone()
        reasons=[]
        if c["response_status"]!="answered":reasons.append("FUP-08")
        if material:reasons.append("FUP-04")
        if "forecast_vs_actual" in flags:reasons.append("FUP-05")
        if "conditional_unclear" in flags or (card["conditionalRequests"] and not any(x in current for x in card["conditionalRequests"])):reasons.append("FUP-06")
        if "incomparable_basis" in flags:reasons.append("FUP-03")
        if missing:reasons.append("FUP-02")
        if not current or "assertion_only" in flags:reasons.append("FUP-01")
        if "vague_claim" in flags:reasons.append("FUP-07")
        if review and review["decision"]=="return":reasons.append("FUP-09")
        if not reasons:reasons.append("FUP-10")
        fs=list(self.db.execute("SELECT f.*,a.id AS answer_id FROM interview_followups f LEFT JOIN interview_followup_answers a ON a.followup_id=f.id WHERE f.claim_id=? ORDER BY f.created_at",(claim,)))
        open_turn=next((x for x in fs if x["answer_id"] is None),None)
        addressed={f["trigger_id"] for f in fs if f["answer_id"] is not None}
        trigger=next((x for x in reasons if x not in addressed),None)
        return {"claimId":claim,"openFollowUpId":open_turn["id"] if open_turn else None,"triggerId":None if open_turn else trigger,"question":None if open_turn or not trigger else card["targetedFollowUp"] if trigger in {"FUP-01","FUP-02","FUP-03","FUP-05","FUP-06","FUP-07"} else self.triggers[trigger]["action"],"reason":None if not trigger else self.triggers[trigger]["trigger"],"requestIds":card["primaryRequests"]+card["supplementaryRequests"]+card["conditionalRequests"],"unresolvedTriggers":reasons,"scoringEligible":False,"source":"approved rule-driven proposal; human selects/records, not an automatic message"}
    def draft_model_wording(self,token,assessment,claim):
        if not self.dp.enable_narrative:raise self.Invalid("Local model disabled; synthetic opt-in required")
        with self.db:
            a=self._actor(token,assessment,{"assessor"});c=self._claim(assessment,claim);s=self.suggest(token,assessment,claim)
            if not s["triggerId"] or s["openFollowUpId"]:raise self.Invalid("No current eligible follow-up trigger")
            if c["response_status"]!="answered":raise self.Invalid("Use the approved rule for absent or declined response")
            verbatim=self._decrypt(c["response_id"],"verbatim",c["verbatim"])
            try:r=propose_wording(verbatim,s["triggerId"],s["reason"],s["question"],s["requestIds"])
            except NarrativeUnavailable as e:raise self.Invalid(str(e)) from e
            id=newid()
            self.db.execute("INSERT INTO interview_model_proposals VALUES (?,?,?,?,?,?,?,?)",(id,claim,s["triggerId"],r["model"],r["modelDigest"],self._encrypt(id,"payload",json.dumps(r,ensure_ascii=False)),a["id"],self.dp.clock()))
            self.dp._audit(assessment,a["id"],"draft interview model wording proposed",id)
            return {"proposalId":id,**r}
    def record_followup(self,token,assessment,claim,trigger,question,proposal=None):
        with self.db:
            a=self._actor(token,assessment,{"assessor"});s=self.suggest(token,assessment,claim)
            if s["openFollowUpId"] or not trigger or trigger!=s["triggerId"]:raise self.Invalid("Only one open follow-up, current suggested trigger required")
            question=self.required(question,"human-confirmed follow-up question")
            if proposal is not None:
                p=self.db.execute("SELECT * FROM interview_model_proposals WHERE id=? AND claim_id=? AND trigger_id=?",(proposal,claim,trigger)).fetchone()
                if not p:raise self.Invalid("Proposal must match current claim and trigger")
            id=newid();self.db.execute("INSERT INTO interview_followups VALUES (?,?,?,?,?,?,?,?)",(id,claim,trigger,self._encrypt(id,"question",question),s["reason"],json.dumps(s["requestIds"]),a["id"],self.dp.clock()))
            if proposal is not None:self.db.execute("INSERT INTO interview_proposal_links VALUES (?,?)",(id,proposal))
            self.dp._audit(assessment,a["id"],"interview follow-up approved for capture",id);return id
    def answer(self,token,assessment,followup,status,verbatim):
        if status not in {"answered","unknown","declined"}:raise self.Invalid("Invalid follow-up answer status")
        if status=="answered":self.required(verbatim,"verbatim follow-up response")
        elif not isinstance(verbatim,str) or len(verbatim)>4000:raise self.Invalid("Response text invalid")
        with self.db:
            a=self._actor(token,assessment,{"assessor"})
            f=self.db.execute("SELECT * FROM interview_followups WHERE id=?",(followup,)).fetchone()
            if not f:raise self.Denied("Access denied")
            self._claim(assessment,f["claim_id"])
            if self.db.execute("SELECT 1 FROM interview_followup_answers WHERE followup_id=?",(followup,)).fetchone():raise self.Invalid("Follow-up response immutable")
            id=newid();self.db.execute("INSERT INTO interview_followup_answers VALUES (?,?,?,?,?,?)",(id,followup,self._encrypt(id,"verbatim",verbatim),status,a["id"],self.dp.clock()))
            self.dp._audit(assessment,a["id"],"interview follow-up response captured",id);return id
    def review_capture(self,token,assessment,claim,decision,reason,confirmed=False):
        if decision not in {"confirm_capture","return"}:raise self.Invalid("Invalid capture review decision")
        with self.db:
            a=self._actor(token,assessment,{"reviewer"});c=self._claim(assessment,claim)
            if a["id"]==c["author"]:raise self.Denied("Independent reviewer required")
            if self.db.execute("SELECT 1 FROM interview_capture_reviews WHERE claim_id=?",(claim,)).fetchone():raise self.Invalid("Capture already reviewed")
            if decision=="confirm_capture" and confirmed is not True:raise self.Invalid("Confirm only accuracy of capture, not evidence sufficiency")
            id=newid();self.db.execute("INSERT INTO interview_capture_reviews VALUES (?,?,?,?,?,?)",(id,claim,a["id"],decision,self._encrypt(id,"reason",self.required(reason,"review rationale")),self.dp.clock()))
            self.dp._audit(assessment,a["id"],"interview capture review "+decision,id)
            return id
    def view(self,token,assessment):
        self._actor(token,assessment,{"assessor","reviewer","owner"})
        sessions=[dict(s) for s in self.db.execute("SELECT id,persona,stakeholder_ref AS stakeholderRef,role,scope,created_at FROM interview_sessions WHERE assessment_id=? ORDER BY created_at",(assessment,))]
        claims=[]
        for r in self.db.execute("SELECT c.id FROM interview_claims c JOIN interview_responses r ON r.id=c.response_id JOIN interview_sessions s ON s.id=r.session_id WHERE s.assessment_id=? ORDER BY c.created_at",(assessment,)):
            c=self._claim(assessment,r["id"]);rev=self.db.execute("SELECT id,decision,reason FROM interview_capture_reviews WHERE claim_id=?",(c["id"],)).fetchone()
            followups=[]
            for f in self.db.execute("SELECT id,trigger_id,question,reason,request_ids FROM interview_followups WHERE claim_id=? ORDER BY created_at",(c["id"],)):
                ans=self.db.execute("SELECT id,verbatim,status FROM interview_followup_answers WHERE followup_id=?",(f["id"],)).fetchone();pl=self.db.execute("SELECT p.id AS proposal_id,p.payload FROM interview_proposal_links l JOIN interview_model_proposals p ON p.id=l.proposal_id WHERE l.followup_id=?",(f["id"],)).fetchone()
                followups.append({**dict(f),"modelProposalId":pl["proposal_id"] if pl else None,"modelProposal":json.loads(self._decrypt(pl["proposal_id"],"payload",pl["payload"])) if pl else None,"question":self._decrypt(f["id"],"question",f["question"]),"answer":{"status":ans["status"],"verbatim":self._decrypt(ans["id"],"verbatim",ans["verbatim"])} if ans else None})
            claims.append({"id":c["id"],"sessionId":c["session_id"],"persona":c["persona"],"stakeholderRef":c["stakeholder_ref"],"role":c["role"],"questionId":c["question_id"],"question":self.cards[c["question_id"]]["question"],"verbatim":self._decrypt(c["response_id"],"verbatim",c["verbatim"]),"responseStatus":c["response_status"],"interpretation":self._decrypt(c["id"],"interpretation",c["interpretation"]),"claimClass":c["claim_class"],"links":self._linked(c["id"],assessment),"captureReview":{"decision":rev["decision"],"reason":self._decrypt(rev["id"],"reason",rev["reason"])} if rev else None,"followUps":followups,"suggestion":self.suggest(token,assessment,c["id"]),"scoringEligible":False,"validationStatus":"unverified interview claim"})
        conflicts=[{**dict(r),"topic":self._decrypt(r["id"],"topic",r["topic"]),"status":self.dp.validation.conflict_status(assessment,r["id"])} for r in self.db.execute("SELECT id,claim_a AS claimA,claim_b AS claimB,topic,material FROM interview_conflicts WHERE assessment_id=? ORDER BY created_at",(assessment,))]
        return {"method":METHOD,"questions":list(self.cards.values()),"sessions":sessions,"claims":claims,"conflicts":conflicts,"scoringEligible":False}
