"""Opt-in fictional Aurora source exercise and isolated mock structural integration."""
import hashlib,json
from pathlib import Path
from decimal import Decimal
from openpyxl import load_workbook
from scoring import weighted_dimensions

HERE=Path(__file__).resolve().parent
INPUT=json.loads((HERE/"AURORA-PILOT-INPUTS.json").read_text())

def load_rows(path):
    raw=Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest()!=INPUT["interviewSource"]["sha256"]:raise ValueError("Aurora workbook fingerprint mismatch")
    workbook=load_workbook(path,read_only=True,data_only=True)
    try:rows=list(workbook["Interview test"].iter_rows(min_row=8,max_row=36,values_only=True))
    finally:workbook.close()
    if len(rows)!=29 or {r[0] for r in rows}!=set(INPUT["mapping"]):raise ValueError("Aurora workbook row mapping mismatch")
    return rows

def source_case(dp,aid,t,path):
    """Record workbook claims only; all decisions in this test are scripted fictional actions."""
    by={q:[] for q in dp.rules};flags={q:False for q in dp.rules};personas={};claims={};rows=load_rows(path)
    for row in rows:
        iq,dimension,role,question,response,pointers,source_class,conflict,*_=row
        q=INPUT["mapping"][iq]
        if role not in personas:personas[role]=dp.interviews.start(t["assessor"],aid,role,"AURORA-FICTIONAL-"+str(len(personas)+1),role,"Workbook interview dry run")
        observations=["assertion_only"]+(["forecast_vs_actual"] if iq in ("IQ25","IQ26","IQ29") else [])
        interpretation=f"Workbook Interview test {iq}, row {int(iq[2:])+7}. Original question: {question} Referenced but unavailable source records: {pointers}. Workbook class {source_class} is illustrative, not verified. Workbook conflict flag: {conflict}."
        cid=dp.interviews.record(t["assessor"],aid,personas[role],q,"answered",response,interpretation,observations,[])
        dp.interviews.review_capture(t["reviewer"],aid,cid,"confirm_capture","Scripted synthetic capture check against workbook only",True)
        by[q].append(cid);claims[iq]=cid;flags[q]|=conflict=="Yes"
    iq26=rows[25];role=iq26[2]
    extra=dp.interviews.record(t["assessor"],aid,personas[role],"Q25","answered",iq26[4],"Cross-reference IQ26 row 33: programme explains composition of its reported benefit; not independent corroboration.",["assertion_only","forecast_vs_actual"],[])
    dp.interviews.review_capture(t["reviewer"],aid,extra,"confirm_capture","Scripted source capture only",True);by["Q25"].append(extra)
    conflict=dp.interviews.conflict(t["assessor"],aid,claims["IQ25"],extra,"Programme reported versus Finance-validated benefit; forecast and actual basis unresolved",True)
    suggestion=dp.interviews.suggest(t["assessor"],aid,claims["IQ25"])
    if suggestion["triggerId"]:dp.interviews.record_followup(t["assessor"],aid,claims["IQ25"],suggestion["triggerId"],suggestion["question"])
    for q,ids in by.items():
        body={"applicability":"applicable","condition":"unknown","evidenceClass":"E3" if ids else "E4","strength":"Not assessed","fieldsVerified":False,"comparable":False,"materialityReviewed":False,"requiresCorroboration":True,"documentaryConflict":flags[q],"claim":"Unverified workbook interview context" if ids else "No direct workbook response","rationale":"Referenced source documents were not supplied; workbook assertions and illustrative classifications cannot validate this criterion.","owner":dp.rules[q]["stakeholder"],"followUp":dp.rules[q]["followUp"],"conditionalApplies":None,"refs":[],"claimIds":ids}
        dp.validation.draft(t["assessor"],aid,q,body)
        for req in dp.rules[q]["primary"]:
            if not any(r["id"]==req and r["status"]=="requested" for r in dp.catalogue_view(t["assessor"],aid)["requests"]):dp.mark_request(t["assessor"],aid,req,"requested","Underlying fictional source referenced but not supplied")
    s=dp.executive.snapshot(t["owner"],aid)[0]
    b=dp.executive.draft(t["assessor"],aid,{"title":"Aurora workbook dry run — evidence gaps","summary":"The fictional interviews report stable technical delivery alongside disputed adoption and benefit evidence. No underlying records were supplied; this is a claim-based review, not a validated assessment.","limitations":"All 28 criteria remain unsupported. The workbook's own illustrative judgements and calibration arithmetic are not independently validated outcomes.","findingIds":[],"options":[{"direction":"Correct","rationale":"Consider corrective work only after the underlying sources are verified","consequences":"Cannot substantiate a substantive direction on current evidence"},{"direction":"Reassess","rationale":"Obtain and independently review primary documents and resolve benefit discrepancy","consequences":"Withhold assessment score and substantive direction"}],"actions":[{"condition":"Reconcile reported and validated benefit on comparable basis","owner":"Fictional Finance and programme owners","followUp":"Request benefits tracker, Finance validation and baseline definitions"},{"condition":"Verify adoption against usage and target population","owner":"Fictional business owner","followUp":"Request usage analytics and training records separately"}]})
    dp.executive.review(t["reviewer"],aid,b,"accept","Scripted synthetic review of gaps, not acceptance of workbook claims",True)
    dp.executive.direction(t["owner"],aid,b,"Reassess","Scripted fictional owner choice to obtain underlying evidence","No score or investment recommendation; verify source records",True)
    # Dates are deliberately not inferred: workbook gives month 18, not calendar periods.
    return {"rows":len(rows),"claims":len(dp.interviews.view(t["owner"],aid)["claims"]),"coveredCriteria":sum(bool(x) for x in by.values()),"dimensions":len({r["dimension"] for r in dp.rules.values()}),"supported":s["supportedCount"],"conflict":conflict,"brief":b,"calibrationArithmetic":str(weighted_dimensions(json.loads((HERE/"SCORING-CALIBRATION-FIXTURES.json").read_text())["cases"][1]["scores"],dp.scoring.weights)),"pilotScore":dp.scoring.view(t["owner"],aid).get("canonical"),"followUp":"No independently documented calendar follow-up supplied; do not invent one"}
