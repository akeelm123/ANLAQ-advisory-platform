const {test}=require("node:test"),a=require("node:assert/strict"),{spec,getRule,assess}=require("./draft-validator.cjs");
const expected={MET:"supported_met","NOT-MET":"supported_not_met",MISSING:"insufficient",CONFLICT:"contradiction"};
function supported(id){
 const r=getRule(id);
 return {criterionId:id,applicability:"applicable",openMaterialContradiction:false,refs:[...r.primary,...r.supplementary.slice(0,1)].map((requestId,i)=>({requestId,evidenceId:"SYN-"+i,locator:"synthetic p. "+(i+1)})),conditionalApplies:false,conditionalRationale:"Synthetic scenario; AI not in scope",fieldsVerified:true,comparable:true,evidenceClass:"E2",evidenceStrength:"Moderate",requiresCorroboration:true,independenceConfirmed:true,materialityReviewed:true,author:"Synthetic assessor",reviewer:"Synthetic reviewer",reviewerAccepted:true,reviewReason:"Synthetic structured assumptions",condition:"met"};
}
test("complete and unique specification, 28 rules and 112 scenario definitions",()=>{a.equal(spec.rules.length,28);a.equal(new Set(spec.rules.map(r=>r.ruleId)).size,28);a.equal(spec.scenarios.length,112);a.equal(new Set(spec.scenarios.map(s=>s.id)).size,112);a.equal(spec.rules.reduce((n,r)=>n+r.primary.length+r.supplementary.length+r.conditional.length,0),89);});
for(const sc of spec.scenarios){
 const kind=sc.id.replace(sc.ruleId+"-","");
 test(sc.id+" structured control fixture",()=>{let f=supported(sc.criterionId);if(kind==="NOT-MET")f.condition="not_met";if(kind==="MISSING")f.refs=[];if(kind==="CONFLICT")f.openMaterialContradiction=true;const r=assess(f);a.equal(r.state,expected[kind]);a.equal(r.scoringEligible,false);a.equal(r.draft,true);});
}
test("review pending with same name, missing acknowledgement or rationale",()=>{for(const override of [{reviewer:"Synthetic assessor"},{reviewerAccepted:false},{reviewReason:""}])a.equal(assess({...supported("Q01"),...override}).state,"review_pending");});
test("E3/E4 claims cannot produce supported judgement",()=>{for(const evidenceClass of ["E3","E4"])a.equal(assess({...supported("Q01"),evidenceClass}).state,"insufficient");});
test("E1 adverse supported evidence is not missing and separate strength remains independent",()=>{a.equal(assess({...supported("Q01"),condition:"not_met",evidenceClass:"E1",evidenceStrength:"Weak"}).state,"supported_not_met");});
test("conditional AI source applicable, missing and out-of-scope cases",()=>{const f=supported("Q20");a.equal(assess({...f,conditionalApplies:true}).state,"insufficient");a.equal(assess({...f,conditionalRationale:""}).state,"insufficient");a.equal(assess({...f,conditionalApplies:true,refs:[...f.refs,{requestId:"DC-05",evidenceId:"SYN-AI",locator:"p.3"}]}).state,"supported_met");});
test("unknown applicability, N/A and unapproved denominator",()=>{a.equal(assess({...supported("Q01"),applicability:"unknown"}).state,"insufficient");a.equal(assess({...supported("Q01"),applicability:"not_applicable"}).state,"exception_pending");});
test("reject unmapped source, missing locator, false independence and no decision",()=>{for(const override of [{refs:[{requestId:"LC-01",evidenceId:"x",locator:"p1"}]},{refs:[{requestId:"SA-01",evidenceId:"x",locator:""}]},{independenceConfirmed:false},{condition:"unknown"}])a.equal(assess({...supported("Q01"),...override}).state,"insufficient");});
test("open contradiction takes precedence; no score or release",()=>{const r=assess({...supported("Q01"),openMaterialContradiction:true,condition:"not_met"});a.equal(r.state,"contradiction");a.equal(r.scoringEligible,false);});

test("alternative must be mapped, cited, reviewed and justified",()=>{const f=supported("Q01");f.refs=[{requestId:"SA-02",evidenceId:"SYN-A",locator:"p1"},{requestId:"SA-03",evidenceId:"SYN-B",locator:"p2"}];a.equal(assess({...f,acceptedAlternative:true}).state,"insufficient");a.equal(assess({...f,acceptedAlternative:true,alternativeRationale:"Synthetic equivalent",alternativeReviewerAccepted:true}).state,"supported_met");});
