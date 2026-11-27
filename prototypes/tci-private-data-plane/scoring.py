"""Restricted synthetic scoring: independently reviewed judgement, exact weighted arithmetic."""
from decimal import Decimal
from uuid import uuid4

METHOD="0.5.0-alpha.1"
def dec(x):return Decimal(str(x))
def weighted_dimensions(scores,weights):
    if set(scores)!=set(weights) or sum(dec(v) for v in weights.values())!=100:raise ValueError("Complete dimension coverage and weights required")
    if any(isinstance(v,bool) or not dec(1)<=dec(v)<=dec(5) for v in scores.values()):raise ValueError("Dimension score outside scale")
    return sum(dec(scores[d])*dec(weights[d])/100 for d in weights)

class ScoringWorkflow:
    def __init__(self,dp,reg,invalid,denied,required,enabled=False):
        self.dp=dp;self.db=dp.db;self.Invalid=invalid;self.Denied=denied;self.required=required;self.enabled=enabled is True
        self.criteria={c["id"]:c for c in reg["criteria"]};self.weights=reg["weights"];self.anchors={(a[0],a[1]):a for a in reg["responseAnchors"]}
        self.lenses={name:{r[0]:dec(r[i])*100 for r in reg["personaWeights"]} for i,name in enumerate(["Board","CIO","Chief Platform Officer","Transformation Office"],1)}
        if len(self.criteria)!=28 or len(self.weights)!=7 or len(self.anchors)!=140 or sum(self.weights.values())!=100:raise invalid("Invalid approved scoring structure")
        for d in self.weights:
            if sum(c["criterionWeight"] for c in self.criteria.values() if c["dimension"]==d)!=100:raise invalid("Invalid criterion weights")
        if any(sum(w.values())!=100 for w in self.lenses.values()):raise invalid("Invalid persona weights")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS pilot_score_drafts(id TEXT PRIMARY KEY,assessment_id TEXT NOT NULL REFERENCES assessments(id),validation_id TEXT NOT NULL REFERENCES validation_drafts(id),criterion TEXT NOT NULL,author TEXT NOT NULL REFERENCES users(id),payload TEXT NOT NULL,created_at REAL NOT NULL);
        CREATE TABLE IF NOT EXISTS pilot_score_reviews(id TEXT PRIMARY KEY,draft_id TEXT UNIQUE NOT NULL REFERENCES pilot_score_drafts(id),reviewer TEXT NOT NULL REFERENCES users(id),decision TEXT NOT NULL,payload TEXT NOT NULL,created_at REAL NOT NULL);
        """)
        for table in ("pilot_score_drafts","pilot_score_reviews"):
            self.db.executescript(f"CREATE TRIGGER IF NOT EXISTS {table}_immutable_update BEFORE UPDATE ON {table} BEGIN SELECT RAISE(ABORT,'immutable pilot score'); END; CREATE TRIGGER IF NOT EXISTS {table}_immutable_delete BEFORE DELETE ON {table} BEGIN SELECT RAISE(ABORT,'immutable pilot score'); END;")
    def _actor(self,token,aid,roles):
        a=self.dp._actor(token,aid,roles)
        if not self.enabled:raise self.Denied("Synthetic pilot scoring disabled")
        return a
    def _current_validation(self,aid,q):
        r=self.db.execute("SELECT * FROM validation_drafts WHERE assessment_id=? AND criterion=? ORDER BY created_at DESC,rowid DESC LIMIT 1",(aid,q)).fetchone()
        if not r:return None,None
        p=self.dp.validation._open(r["id"],r["payload"])
        rev=self.db.execute("SELECT * FROM validation_reviews WHERE draft_id=?",(r["id"],)).fetchone()
        if not rev or rev["decision"]!="accept":return r["id"],None
        controls=self.dp.validation._open(rev["id"],rev["payload"])["controls"]
        state=self.dp.validation._evaluate(aid,q,p,controls)["state"]
        return r["id"],state if state in ("supported_met","supported_not_met") else None
    def _eligible(self,aid,q,vid,score,operating):
        current,state=self._current_validation(aid,q)
        if current!=vid or not state:raise self.Invalid("Latest criterion finding must have current independent evidence acceptance")
        if type(score) is not int or score not in range(1,6):raise self.Invalid("Explicit integer anchor 1–5 required")
        if (score>=3)!=(state=="supported_met"):raise self.Invalid("Score must reflect supported minimum condition; unknown is not poor performance")
        if score>=4 and operating is not True:raise self.Invalid("Sustained operating evidence required for 4–5")
    def draft(self,token,aid,q,vid,score,rationale,operating,red_flag):
        with self.db:
            a=self._actor(token,aid,{"assessor"})
            if q not in self.criteria or type(operating) is not bool or not isinstance(red_flag,str) or len(red_flag)>4000:raise self.Invalid("Structured scoring inputs required")
            self._eligible(aid,q,vid,score,operating)
            id=uuid4().hex;p={"score":score,"rationale":self.required(rationale,"anchor-specific rationale"),"operating":operating,"redFlag":red_flag.strip()}
            self.db.execute("INSERT INTO pilot_score_drafts VALUES (?,?,?,?,?,?,?)",(id,aid,vid,q,a["id"],self.dp.validation._seal(id,p),self.dp.clock()))
            self.dp._audit(aid,a["id"],"synthetic score draft",id);return id
    def review(self,token,aid,id,decision,reason,confirmed,operating_confirmed):
        with self.db:
            a=self._actor(token,aid,{"reviewer"})
            r=self.db.execute("SELECT * FROM pilot_score_drafts WHERE id=? AND assessment_id=?",(id,aid)).fetchone()
            if not r or a["id"]==r["author"]:raise self.Denied("Independent reviewer required")
            if decision not in ("accept","return") or self.db.execute("SELECT 1 FROM pilot_score_reviews WHERE draft_id=?",(id,)).fetchone():raise self.Invalid("Invalid or duplicate score review")
            p=self.dp.validation._open(id,r["payload"])
            if decision=="accept":
                self._eligible(aid,r["criterion"],r["validation_id"],p["score"],p["operating"])
                if confirmed is not True or (p["score"]>=4 and operating_confirmed is not True):raise self.Invalid("Explicit independent anchor and operating evidence confirmation required")
                _,vp=self.dp.validation._draft_row(aid,r["validation_id"])
                if not self.dp.validation._previewed(a,aid,vp["refs"]):raise self.Invalid("Reviewer must preview cited evidence")
            rid=uuid4().hex;self.db.execute("INSERT INTO pilot_score_reviews VALUES (?,?,?,?,?,?)",(rid,id,a["id"],decision,self.dp.validation._seal(rid,{"reason":self.required(reason,"review rationale"),"confirmed":confirmed is True,"operatingConfirmed":operating_confirmed is True}),self.dp.clock()))
            self.dp._audit(aid,a["id"],"synthetic score "+decision,rid);return rid
    def view(self,token,aid):
        self.dp._actor(token,aid,{"assessor","reviewer","owner"})
        if not self.enabled:return {"enabled":False,"finalScoringLocked":True}
        rows=[];accepted={};flags=[];eligible=[]
        for q,c in self.criteria.items():
            vid,state=self._current_validation(aid,q)
            if state:eligible.append({"criterion":q,"validationId":vid,"condition":state,"anchors":[{"score":n,"label":self.anchors[q,n][2],"description":self.anchors[q,n][3],"example":self.anchors[q,n][5]} for n in range(1,6)]})
            latest=None
            for r in self.db.execute("SELECT * FROM pilot_score_drafts WHERE assessment_id=? AND criterion=? ORDER BY created_at,rowid",(aid,q)):
                p=self.dp.validation._open(r["id"],r["payload"]);rv=self.db.execute("SELECT * FROM pilot_score_reviews WHERE draft_id=?",(r["id"],)).fetchone()
                status="review_pending"
                try:self._eligible(aid,q,r["validation_id"],p["score"],p["operating"])
                except self.Invalid:status="withheld"
                if rv and status!="withheld":status="accepted" if rv["decision"]=="accept" else "returned"
                item={"id":r["id"],"criterion":q,"validationId":r["validation_id"],"payload":p,"state":status,"review":self.dp.validation._open(rv["id"],rv["payload"]) if rv else None}
                rows.append(item);latest=item
            if latest and latest["state"]=="accepted":
                accepted[q]=latest["payload"]["score"]
                if latest["payload"]["redFlag"]:flags.append({"criterion":q,"flag":latest["payload"]["redFlag"]})
        dimensions={}
        for d in self.weights:
            group={q:c for q,c in self.criteria.items() if c["dimension"]==d}
            dimensions[d]=sum(dec(accepted[q])*dec(c["criterionWeight"])/100 for q,c in group.items()) if set(group)<=accepted.keys() else None
        overall=None;weakest=[];lenses={}
        if all(v is not None for v in dimensions.values()):
            overall=weighted_dimensions(dimensions,self.weights);weakest=[d for d,v in dimensions.items() if v==min(dimensions.values())]
            lenses={name:str(weighted_dimensions(dimensions,w)) for name,w in self.lenses.items()}
        return {"enabled":True,"method":METHOD,"finalScoringLocked":True,"eligible":eligible,"records":rows,"coverage":len(accepted),"dimensions":{d:str(v) if v is not None else None for d,v in dimensions.items()},"canonical":str(overall) if overall is not None else None,"weakestDimensions":weakest,"redFlags":flags,"personaLenses":lenses,"thresholds":"Unapproved; no automated band, cap or decision."}
