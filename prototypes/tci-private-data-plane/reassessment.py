"""Synthetic periodic snapshots and independently reviewed comparison."""
from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
from uuid import uuid4

METHOD="0.7.0-alpha.1"
SUPPORTED={"supported_met","supported_not_met"}
def fingerprint(x):return sha256(json.dumps(x,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()

class ReassessmentWorkflow:
    def __init__(self,dp,invalid,denied,required):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.Denied=denied;self.required=required
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS reassessment_snapshots(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),author TEXT NOT NULL REFERENCES users(id),state_hash TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reassessment_snapshot_reviews(id TEXT PRIMARY KEY,snapshot_id TEXT UNIQUE NOT NULL REFERENCES reassessment_snapshots(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reassessment_comparisons(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),baseline_id TEXT NOT NULL REFERENCES reassessment_snapshots(id),followup_id TEXT NOT NULL REFERENCES reassessment_snapshots(id),author TEXT NOT NULL REFERENCES users(id),payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS reassessment_comparison_reviews(id TEXT PRIMARY KEY,comparison_id TEXT UNIQUE NOT NULL REFERENCES reassessment_comparisons(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        """)
        for t in ("reassessment_snapshots","reassessment_snapshot_reviews","reassessment_comparisons","reassessment_comparison_reviews"):
            self.db.executescript(f"CREATE TRIGGER IF NOT EXISTS {t}_immutable_update BEFORE UPDATE ON {t} BEGIN SELECT RAISE(ABORT,'immutable reassessment record'); END; CREATE TRIGGER IF NOT EXISTS {t}_immutable_delete BEFORE DELETE ON {t} BEGIN SELECT RAISE(ABORT,'immutable reassessment record'); END;")
    def _live(self,token,aid):
        evidence,h=self.dp.executive.snapshot(token,aid)
        scope=self.db.execute("SELECT title,scope FROM assessments WHERE id=?",(aid,)).fetchone()
        brief=next((b for b in reversed(self.dp.executive.view(token,aid)["briefs"]) if b["state"].startswith("reviewed_")),None)
        executive=None
        if brief:
            executive={"briefId":brief["id"],"state":brief["state"],"direction":brief["direction"] if brief["directionCurrent"] else None,"actions":[{"id":brief["id"]+":"+str(i),**a} for i,a in enumerate(brief["payload"]["actions"],1)]}
        scoring=self.dp.scoring.view(token,aid)
        pilot=None
        if scoring["enabled"]:
            pilot={k:scoring[k] for k in ("method","coverage","canonical","dimensions","weakestDimensions","redFlags","personaLenses")}
            # Capture record identity as well as values so same-score revisions do not invisibly change history.
            pilot["records"]=scoring["records"]
        p={"scope":dict(scope),"evidence":evidence,"evidenceHash":h,"executive":executive,"pilot":pilot}
        return p,fingerprint(p)
    def _period(self,start,end):
        try:
            if not isinstance(start,str) or not isinstance(end,str):raise ValueError
            x,y=date.fromisoformat(start),date.fromisoformat(end)
            if x.isoformat()!=start or y.isoformat()!=end or x>y:raise ValueError
        except (ValueError,TypeError):raise self.Invalid("Use valid ISO period start and end dates")
        return start,end
    def capture(self,token,aid,start,end,label,basis):
        start,end=self._period(start,end)
        with self.db:
            a=self.dp._actor(token,aid,{"assessor"});live,h=self._live(token,aid)
            p={"label":self.required(label,"snapshot label"),"periodStart":start,"periodEnd":end,"basis":self.required(basis,"assessment population / measurement basis"),"state":live}
            id=uuid4().hex;self.db.execute("INSERT INTO reassessment_snapshots VALUES (?,?,?,?,?,?)",(id,aid,a["id"],h,self.dp.validation._seal(id,p),self.dp.clock()))
            self.dp._audit(aid,a["id"],"reassessment snapshot captured",id);return id
    def _record(self,table,aid,id):
        row=self.db.execute(f"SELECT * FROM {table} WHERE id=? AND assessment_id=?",(id,aid)).fetchone()
        if not row:raise self.Denied("Access denied")
        return row,self.dp.validation._open(id,row["payload"])
    def _accepted(self,aid,id):
        row,p=self._record("reassessment_snapshots",aid,id)
        r=self.db.execute("SELECT * FROM reassessment_snapshot_reviews WHERE snapshot_id=?",(id,)).fetchone()
        if not r or r["decision"]!="accept":raise self.Invalid("Independently accepted period snapshot required")
        return row,p
    def _refs(self,p):
        ev=p["state"]["evidence"]
        return [r for c in ev["criteria"] if c["state"] in SUPPORTED for r in c["refs"]]+[r for c in ev["conflicts"] if c["status"]=="resolved" for r in c["resolutions"][-1]["refs"]]
    def review_snapshot(self,token,aid,id,decision,reason,confirmed):
        with self.db:
            a=self.dp._actor(token,aid,{"reviewer"});row,p=self._record("reassessment_snapshots",aid,id)
            if a["id"]==row["author"]:raise self.Denied("Independent reviewer required")
            if decision not in ("accept","return") or self.db.execute("SELECT 1 FROM reassessment_snapshot_reviews WHERE snapshot_id=?",(id,)).fetchone():raise self.Invalid("Invalid or duplicate snapshot review")
            if decision=="accept":
                _,h=self._live(token,aid)
                if h!=row["state_hash"]:raise self.Invalid("Draft snapshot no longer reflects current evidence; recapture")
                if confirmed is not True or not self.dp.validation._previewed(a,aid,self._refs(p)):raise self.Invalid("Independent period, scope and source review required")
            rid=uuid4().hex;self.db.execute("INSERT INTO reassessment_snapshot_reviews VALUES (?,?,?,?,?,?)",(rid,id,a["id"],decision,self.dp.validation._seal(rid,{"reason":self.required(reason,"snapshot review rationale"),"confirmed":confirmed is True}),self.dp.clock()))
            self.dp._audit(aid,a["id"],"reassessment snapshot "+decision,rid);return rid
    def _compare(self,b,f):
        x,y=b["state"],f["state"]
        if b["periodEnd"]>=f["periodStart"]:raise self.Invalid("Baseline and follow-up periods must be strictly ordered and non-overlapping")
        if x["scope"]!=y["scope"] or x["evidence"]["registerHash"]!=y["evidence"]["registerHash"] or x["evidence"]["specHash"]!=y["evidence"]["specHash"]:raise self.Invalid("Comparable scope and methodology required")
        if b["basis"].strip().casefold()!=f["basis"].strip().casefold():raise self.Invalid("Matching assessment population and measurement basis required")
        by={c["criterion"]:c for c in x["evidence"]["criteria"]};rows=[];dimensions={}
        for c in y["evidence"]["criteria"]:
            old=by[c["criterion"]];s,t=old["state"],c["state"]
            if s not in SUPPORTED or t not in SUPPORTED:
                change="support_gained" if t in SUPPORTED else "support_lost" if s in SUPPORTED else "unresolved_both"
            elif s==t:change="condition_unchanged"
            else:change="condition_improved" if t=="supported_met" else "condition_deteriorated"
            rows.append({"criterion":c["criterion"],"dimension":c["dimension"],"baseline":old,"followUp":c,"change":change})
        for d in self.dp.scoring.weights:
            group=[r for r in rows if r["dimension"]==d]
            counts={k:sum(r["change"]==k for r in group) for k in ("condition_improved","condition_deteriorated","condition_unchanged","support_gained","support_lost","unresolved_both")}
            dimensions[d]={"baselineSupported":sum(r["baseline"]["state"] in SUPPORTED for r in group),"followUpSupported":sum(r["followUp"]["state"] in SUPPORTED for r in group),"criteria":len(group),"changes":counts}
        pilot=None
        if all(s["pilot"] and s["pilot"]["coverage"]==28 and s["pilot"]["canonical"] is not None for s in (x,y)) and x["pilot"]["method"]==y["pilot"]["method"]:
            pilot={"baseline":x["pilot"]["canonical"],"followUp":y["pilot"]["canonical"],"delta":str(Decimal(y["pilot"]["canonical"])-Decimal(x["pilot"]["canonical"])),"dimensions":{d:str(Decimal(y["pilot"]["dimensions"][d])-Decimal(x["pilot"]["dimensions"][d])) for d in dimensions},"provisional":True}
        return {"criteria":rows,"dimensions":dimensions,"pilot":pilot,"automaticDecision":False}
    def compare(self,token,aid,baseline,followup,rationale,confirmed,actions):
        with self.db:
            a=self.dp._actor(token,aid,{"assessor"});_,b=self._accepted(aid,baseline);_,f=self._accepted(aid,followup)
            if confirmed is not True:raise self.Invalid("Assessor must confirm the same scope, population, measurement basis and methodology")
            result=self._compare(b,f)
            baseline_actions=(b["state"]["executive"] or {}).get("actions",[])
            if not isinstance(actions,list) or any(not isinstance(o,dict) for o in actions):raise self.Invalid("Structured baseline action follow-up required")
            ids=[o.get("actionId") for o in actions]
            if any(not isinstance(id,str) for id in ids) or len(ids)!=len(set(ids)) or set(ids)!={o["id"] for o in baseline_actions}:raise self.Invalid("Account for each baseline action exactly once")
            eligible={c["validationId"] for c in f["state"]["evidence"]["criteria"] if c["state"] in SUPPORTED}
            tracked=[]
            for o in actions:
                status=o.get("status");refs=o.get("findingIds")
                if status not in ("open","in_progress","closed","unknown") or not isinstance(refs,list) or any(not isinstance(v,str) for v in refs) or not set(refs)<=eligible:raise self.Invalid("Invalid action state or follow-up evidence")
                if status=="closed" and not refs:raise self.Invalid("Verified closure requires current independently supported follow-up finding")
                tracked.append({**next(x for x in baseline_actions if x["id"]==o["actionId"]),"status":status,"rationale":self.required(o.get("rationale"),"action status rationale"),"findingIds":refs})
            id=uuid4().hex;p={"rationale":self.required(rationale,"comparison rationale and limitations"),"basisConfirmed":True,"result":result,"actions":tracked}
            self.db.execute("INSERT INTO reassessment_comparisons VALUES (?,?,?,?,?,?,?)",(id,aid,baseline,followup,a["id"],self.dp.validation._seal(id,p),self.dp.clock()))
            self.dp._audit(aid,a["id"],"reassessment comparison drafted",id);return id
    def review_comparison(self,token,aid,id,decision,reason,confirmed):
        with self.db:
            a=self.dp._actor(token,aid,{"reviewer"});row,p=self._record("reassessment_comparisons",aid,id)
            if row["author"]==a["id"]:raise self.Denied("Independent reviewer required")
            if decision not in ("accept","return") or self.db.execute("SELECT 1 FROM reassessment_comparison_reviews WHERE comparison_id=?",(id,)).fetchone():raise self.Invalid("Invalid or duplicate comparison review")
            if decision=="accept":
                _,b=self._accepted(aid,row["baseline_id"]);_,f=self._accepted(aid,row["followup_id"])
                if confirmed is not True or not self.dp.validation._previewed(a,aid,self._refs(b)+self._refs(f)):raise self.Invalid("Independent comparable-basis, source and action closure review required")
            rid=uuid4().hex;self.db.execute("INSERT INTO reassessment_comparison_reviews VALUES (?,?,?,?,?,?)",(rid,id,a["id"],decision,self.dp.validation._seal(rid,{"reason":self.required(reason,"comparison review rationale"),"confirmed":confirmed is True}),self.dp.clock()))
            self.dp._audit(aid,a["id"],"reassessment comparison "+decision,rid);return rid
    def view(self,token,aid):
        self.dp._actor(token,aid,{"assessor","reviewer","owner"})
        _,h=self._live(token,aid);snaps=[];comparisons=[]
        for r in self.db.execute("SELECT * FROM reassessment_snapshots WHERE assessment_id=? ORDER BY created_at,rowid",(aid,)):
            p=self.dp.validation._open(r["id"],r["payload"]);rv=self.db.execute("SELECT * FROM reassessment_snapshot_reviews WHERE snapshot_id=?",(r["id"],)).fetchone()
            status=("accepted" if rv["decision"]=="accept" else "returned") if rv else ("review_pending" if r["state_hash"]==h else "draft_superseded")
            snaps.append({"id":r["id"],"stateHash":r["state_hash"],"status":status,"matchesCurrent":r["state_hash"]==h,"payload":p,"review":{**self.dp.validation._open(rv["id"],rv["payload"]),"decision":rv["decision"]} if rv else None})
        for r in self.db.execute("SELECT * FROM reassessment_comparisons WHERE assessment_id=? ORDER BY created_at,rowid",(aid,)):
            rv=self.db.execute("SELECT * FROM reassessment_comparison_reviews WHERE comparison_id=?",(r["id"],)).fetchone()
            comparisons.append({"id":r["id"],"baselineId":r["baseline_id"],"followUpId":r["followup_id"],"status":rv["decision"] if rv else "review_pending","payload":self.dp.validation._open(r["id"],r["payload"]),"review":{**self.dp.validation._open(rv["id"],rv["payload"]),"decision":rv["decision"]} if rv else None})
        return {"method":METHOD,"snapshots":snaps,"comparisons":comparisons,"productionLocked":True}
