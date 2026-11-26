"""Create versioned labelled-text fixtures referencing the exact approved specification."""
import hashlib,json,os,pathlib,re
root=pathlib.Path(__file__).resolve().parent.parent.parent
spec=pathlib.Path(os.environ.get("TCI_SPEC",root/"docs/tci/methodology/validation-v1.0-rc.1/TCI_Evidence_Validation_Specification_v1.0-rc.1.json"))
raw=spec.read_bytes();assert hashlib.sha256(raw).hexdigest()=="8d4e730b5ed3cf38fdb4dcd896fa21bc14bf38689babc24159a460980099b00c"
data=json.loads(raw)
# Independently authored fictional values; no client evidence or true business claims.
V={
"Q01": ["Reduce fictional processing delay","Manual fictional approval queues","Synthetic intake workflow","2026-01-10","Synthetic mandate: shorten processing time"],
"Q02": ["Original 2 workflows; revised 3 workflows","SGD 120000 synthetic investment","Nominal SGD, FY26","2026-01-10; 2026-04-04","20 synthetic cases per month","Synthetic change approval CH-01","Prioritise intake before reporting"],
"Q03": ["OUT-SYN-01","10 fictional days","5 fictional days","6 fictional days","calendar days","FY26 Q2","Synthetic data owner; synthetic outcome owner"],
"Q04": ["BEN-SYN-01","Synthetic business owner","Owner accepted responsibility in mock record","5 fictional days saved","Reassess if agreed outcome is not supported","Synthetic operations owner"],
"Q05": ["DEC-SYN-01","Decision-critical to fictional scope","2026-03-01","2026-03-10","2026-03-09","Synthetic sponsor","Approve fictional scope with documented rationale"],
"Q06": ["ESC-SYN-01","Synthetic capacity constraint","Fictional milestone affected","Synthetic delivery sponsor","2026-02-01","Allocate fictional specialist","Mock closure record CL-01","Two fictional resource days"],
"Q07": ["Synthetic sponsor","Synthetic outcome owner","Synthetic business and technology responsibilities","Mock delegated authority D-01","Synthetic handover H-01","No fictional exceptions recorded"],
"Q08": ["2026-05-01","Mock adoption warning","Review fictional rollout","Synthetic action owner","2026-05-15","Mock closure record and observed result","Fictional steering note"],
"Q09": ["100 fictional requests/minute","Synthetic architecture v2","Mock agreed performance/security/recovery requirements","Synthetic test report: 100 fictional requests/minute","One fictional exception recorded","Mock external integration"],
"Q10": ["Mock availability 99.0%; one incident","FY26 Q2","Synthetic minor incident","Mock recovery target 60 min; result 45 min","Synthetic control assurance report","One documented fictional exception"],
"Q11": ["Two fictional releases/week","3 fictional days","Mock automation coverage 80%","One fictional manual intervention","Two synthetic successful releases","10 fictional platform users","Synthetic engineering cost basis"],
"Q12": ["DEBT-SYN-01","Mock legacy dependency","Synthetic technical owner","Fictional cost exposure","Mock remediation plan","SGD 1000 baseline / SGD 1100 actual","Nominal SGD per month","FY26 Q2"],
"Q13": ["Fictional operations workflow population","100 fictional eligible users","70 fictional active users","Mock completed target workflow within period","FY26 Q2","80 fictional users","Synthetic sampled workflow evidence"],
"Q14": ["Four fictional analyst roles","Three fictional trained roles","One fictional role gap","Mock training and hiring plan","SGD 1000 synthetic funding","Fictional observed capability check","Synthetic HR owner"],
"Q15": ["Before: fictional coordinator; after: fictional owner","Mock approval right","Synthetic operating owner","2026-05-01","Mock approved target operating model","Fictional observed decision workflow"],
"Q16": ["Mock usage 60 to 70 fictional users","Synthetic target workflow","FY26 Q1–Q2","Synthetic BAU owner","Mock handover checkpoint","Small fictional sample"],
"Q17": ["CDE-SYN-01","Synthetic data owner","Mock intake data","Mock accepted responsibility","Fictional completeness metric","Synthetic decision dependency"],
"Q18": ["Mock non-blank field rule","100 fictional records","FY26 Q2","4 fictional exceptions","5 to 4 fictional exceptions","Synthetic owner; 2 fictional days old","Mock decision affected","Fictional remediation action"],
"Q19": ["KPI-SYN-01","Mock source table","Fictional completed case definition","Mock group-by total","Synthetic source-to-report path","v1","FY26 Q2","100 fictional records reconciled"],
"Q20": ["Synthetic intake workflow","Mock least-privilege access roles","Synthetic governance owner","Mock control review evidence","No fictional exceptions","Synthetic data processing","AI not in synthetic scenario scope; applicability unverified"],
"Q21": ["FY26 Q2","Mock cycle-time definition","Four fictional committed releases","2026-04-01; 2026-05-01","4 fictional releases; 3 fictional days","Mock integration dependency"],
"Q22": ["REL-SYN-01","One fictional minor defect","2 fictional hours","FY26 Q2","Mock release acceptance criteria","Zero fictional change failures","Mock remediation action"],
"Q23": ["DEP-SYN-01","Decision-relevant fictional dependency","One fictional milestone","Synthetic accountable owner","2026-06-01","Mock mitigation plan","Mock effect: no fictional delay"],
"Q24": ["Mock assumption of 100 fictional users","Fictional adoption lesson","Mock workflow revision","Synthetic delivery owner","2026-05-05","60 to 70 fictional users","Mock observed improvement"],
"Q25": ["BEN-SYN-01; 10 fictional days","5 fictional days","Calendar days per fictional case","FY26 Q2","Synthetic benefit owner","Mock approved revision CH-01","6 fictional days"],
"Q26": ["BEN-SYN-01","SGD 4000 synthetic realised value","SGD 5000 synthetic target","FY26 Q2","SGD","Mock realised cash basis","Synthetic finance record","Mock finance review label","SGD 2000 fictional forecast, separate"],
"Q27": ["BEN-SYN-01","Mock shorter workflow","10 fictional days before; 6 after","Mock comparable population assumption","Fictional seasonal variation","Synthetic independent review record"],
"Q28": ["Synthetic benefit owner","Mock BAU responsibility accepted","Monthly mock review","SGD 500 synthetic operating support","2026-06-01","Mock post-close outcome measure"]
}
fixtures=[];schema=[]
for r in data["rules"]:
    cid=r["criterionId"]; labels=[f.strip() for f in r["fields"].split(",")]; vals=V[cid]; assert len(labels)==len(vals),(cid,len(labels),len(vals))
    keys=[re.sub(r"[^a-z0-9]+","_",l.casefold()).strip("_") for l in labels]
    assert len(keys)==len(set(keys))
    fields=[{"key":k,"label":l,"sourcePhrase":l} for k,l in zip(keys,labels)]
    schema.append({"criterionId":cid,"ruleId":r["ruleId"],"primary":r["primary"],"supplementary":r["supplementary"],"conditional":r["conditional"],"fields":fields})
    lines=["SYNTHETIC TEST DATA — not an assessment",f"Criterion: {cid}"]
    expected=[]
    for f,v in zip(fields,vals):
        line=f"{f['label']}: {v}";lines.append(line)
        expected.append({"key":f["key"],"value":v,"line":len(lines),"startColumn":len(f["label"])+3,"endColumn":len(line),"excerpt":line})
    lines.append("Unrecognised note: Synthetic noise; no inferred values.")
    fixtures.append({"criterionId":cid,"requestId":r["primary"][0],"text":"\n".join(lines)+"\n","expected":expected})
out=pathlib.Path(__file__).parent
(out/"extraction-schema.json").write_text(json.dumps({"version":"0.2.0-alpha.1","specSha256":hashlib.sha256(raw).hexdigest(),"rules":schema},ensure_ascii=False,indent=2)+"\n")
(out/"golden-fixtures.json").write_text(json.dumps({"version":"0.2.0-alpha.1","scope":"Fictional labelled UTF-8 text; not real documents or semantic extraction","fixtures":fixtures},ensure_ascii=False,indent=2)+"\n")
print("Fixtures",len(fixtures),"fields",sum(len(x["expected"]) for x in fixtures))
