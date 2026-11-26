const {test}=require("node:test"),a=require("node:assert/strict"),T=require("./core.js"),{criteria}=require("./sources.json");
const evidence={criterion:"Q01",title:"Synthetic business case",source:"Sample",version:"1",location:"p.2",owner:"Finance",period:"FY26",note:"Synthetic sample",actor:"Alice",sha256:"a".repeat(64)};
const finding={criterion:"Q01",claim:"Sample documented finding",evidenceClass:"E1",author:"Alice",gap:"None identified",contradiction:"none",action:"Monitor",refs:["EV-001"]};
const decision={finding:"F-001",reviewer:"Bob",decision:"accept",reason:"Reviewed sample",confirmed:true};
function fixture(){const s=T.create();T.addEvidence(s,evidence,criteria);return s;}
test("28 source-derived criterion IDs are unique",()=>{a.equal(criteria.length,28);a.equal(new Set(criteria.map(c=>c.id)).size,28);});
test("requires source provenance and digest",()=>{a.throws(()=>T.addEvidence(T.create(),{...evidence,location:""},criteria));a.throws(()=>T.addEvidence(T.create(),{...evidence,sha256:"fake"},criteria));});
test("rejects unknown criterion",()=>a.throws(()=>T.addEvidence(T.create(),{...evidence,criterion:"invalid"},criteria)));
test("rejects missing or mismatched reference",()=>{const s=fixture();a.throws(()=>T.addFinding(s,{...finding,refs:[]},criteria));a.throws(()=>T.addFinding(s,{...finding,criterion:"Q02"},criteria));});
test("E2 rejects duplicated document or owner",()=>{const s=fixture();T.addEvidence(s,{...evidence,owner:"Operations"},criteria);a.throws(()=>T.addFinding(s,{...finding,evidenceClass:"E2",refs:["EV-001","EV-002"]},criteria));T.addEvidence(s,{...evidence,sha256:"b".repeat(64)},criteria);a.throws(()=>T.addFinding(s,{...finding,evidenceClass:"E2",refs:["EV-001","EV-003"]},criteria));});
test("E2 accepts distinct source and owner for review",()=>{const s=fixture();T.addEvidence(s,{...evidence,owner:"Operations",sha256:"b".repeat(64)},criteria);a.equal(T.addFinding(s,{...finding,evidenceClass:"E2",refs:["EV-001","EV-002"]},criteria).id,"F-001");});
test("unknown evidence may be drafted but not accepted",()=>{const s=T.create();T.addFinding(s,{...finding,evidenceClass:"E4",refs:[]},criteria);a.throws(()=>T.review(s,decision));T.review(s,{...decision,decision:"return"});});
test("assertion cannot be accepted",()=>{const s=fixture();T.addFinding(s,{...finding,evidenceClass:"E3"},criteria);a.throws(()=>T.review(s,decision));});
test("open contradiction blocks acceptance",()=>{const s=fixture();T.addFinding(s,{...finding,contradiction:"open",contradictionDetail:"Conflicting result"},criteria);a.throws(()=>T.review(s,decision));});
test("resolved contradiction requires rationale",()=>a.throws(()=>T.addFinding(fixture(),{...finding,contradiction:"resolved",contradictionDetail:"Difference"},criteria)));
test("self-review and missing confirmation blocked",()=>{const s=fixture();T.addFinding(s,finding,criteria);a.throws(()=>T.review(s,{...decision,reviewer:" ALICE "}));a.throws(()=>T.review(s,{...decision,confirmed:false}));});
test("accepted review is logged, cannot be overwritten; release stays locked",()=>{const s=fixture();T.addFinding(s,finding,criteria);T.review(s,decision);a.equal(s.events.length,3);a.equal(s.reviews.length,1);a.throws(()=>T.review(s,decision));a.deepEqual([T.gates().pilotScoring,T.gates().executiveRelease,T.gates().publicDeployment],[false,false,false]);});
