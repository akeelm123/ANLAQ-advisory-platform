(function(g){
"use strict";
const str = v => typeof v === "string" ? v.trim() : "";
const required = (o,ks) => {for(const k of ks) if(!str(o[k])) throw Error(k+" is required");};
const norm = v => str(v).toLowerCase();
const create = () => ({version:"0.1.0-rc.1",baseline:"1.0-reconstructed-rc.1",scope:null,requestEvents:[],evidence:[],findings:[],reviews:[],events:[]});
const event = (s,action,id,actor) => s.events.push({sequence:s.events.length+1,time:new Date().toISOString(),action,id,actor});
const id = (prefix,list) => prefix+String(list.length+1).padStart(3,"0");
function setScope(s,o){
 if(s.scope)throw Error("Scope already recorded; start a new assessment to change it");
 required(o,["title","decision","boundary","period","owner"]);
 s.scope={title:str(o.title),decision:str(o.decision),boundary:str(o.boundary),period:str(o.period),owner:str(o.owner)};
 event(s,"scope recorded","SCOPE",s.scope.owner);return s.scope;
}
function checkScope(s){if(!s.scope)throw Error("Record assessment scope first");}
function requestState(s,requestId){
 if(s.evidence.some(e=>e.requestId===requestId))return "received";
 return s.requestEvents.filter(e=>e.requestId===requestId).at(-1)?.status||"not requested";
}
function markRequest(s,o,requests){
 checkScope(s);required(o,["requestId","status","actor","reason"]);
 if(!requests.some(r=>r.id===o.requestId))throw Error("Unknown evidence request");
 if(!["requested","missing"].includes(o.status))throw Error("Only requested or missing can be recorded; received is derived from evidence");
 if(requestState(s,o.requestId)==="received")throw Error("Evidence already recorded; use a finding to document quality or gaps");
 const r={requestId:o.requestId,status:o.status,actor:str(o.actor),reason:str(o.reason),id:id("REQ-",s.requestEvents)};
 s.requestEvents.push(r);event(s,"request "+r.status,r.id,r.actor);return r;
}
function addEvidence(s,o,criteria,requests=[]){
 checkScope(s);
 if(o.requestId){
  const req=requests.find(r=>r.id===o.requestId);
  if(!req||!Array.isArray(req.criterionIds)||!req.criterionIds.includes(o.criterion))throw Error("Request must have an approved mapping to this criterion");
 }

 required(o,["criterion","title","source","version","location","owner","period","note","actor","sha256"]);
 if(!criteria.some(c=>c.id===o.criterion)) throw Error("Unknown criterion");
 if(!/^[a-f0-9]{64}$/.test(o.sha256)) throw Error("Invalid source digest");
 const r={...o,id:id("EV-",s.evidence)}; s.evidence.push(r);event(s,"evidence captured",r.id,o.actor);return r;
}
function criterionCoverage(s,criterionId,requests){
 return requests.filter(r=>r.criterionIds.includes(criterionId)).map(r=>({
  requestId:r.id,title:r.title,relationship:r.links.find(l=>l.criterionId===criterionId).relationship,
  received:s.evidence.some(e=>e.requestId===r.id&&e.criterion===criterionId)
 }));
}
function addFinding(s,o,criteria){
 checkScope(s);
 required(o,["criterion","claim","evidenceClass","evidenceStrength","author","gap","contradiction","action"]);
 if(!criteria.some(c=>c.id===o.criterion))throw Error("Unknown criterion");
 if(!["E1","E2","E3","E4"].includes(o.evidenceClass))throw Error("Unknown evidence class");
 if(!["Strong","Moderate","Weak","Not assessed"].includes(o.evidenceStrength))throw Error("Unknown evidence strength");
 if(!["none","open","resolved"].includes(o.contradiction))throw Error("Invalid contradiction status");
 if(o.contradiction!=="none"&&!str(o.contradictionDetail))throw Error("Describe the contradiction");
 if(o.contradiction==="resolved"&&!str(o.resolution))throw Error("Resolution rationale required");
 const refs=[...new Set(o.refs||[])];
 const records=refs.map(k=>s.evidence.find(e=>e.id===k&&e.criterion===o.criterion));
 if(records.some(e=>!e))throw Error("Evidence reference must exist for the same criterion");
 if(["E1","E2","E3"].includes(o.evidenceClass)&&!records.length)throw Error("Evidence reference required");
 if(o.evidenceClass==="E2"&&(new Set(records.map(e=>e.sha256)).size<2||new Set(records.map(e=>norm(e.owner))).size<2))throw Error("E2 requires distinct source documents and owners; independence still requires human judgement");
 const r={...o,refs,id:id("F-",s.findings)};s.findings.push(r);event(s,"finding drafted",r.id,o.author);return r;
}
function review(s,o){
 checkScope(s);
 required(o,["finding","reviewer","decision","reason"]);
 const f=s.findings.find(f=>f.id===o.finding);
 if(!f)throw Error("Unknown finding");
 if(norm(f.author)===norm(o.reviewer))throw Error("A different named reviewer is required");
 if(s.reviews.some(r=>r.finding===f.id))throw Error("Already reviewed; create a new finding for reassessment");
 if(!["accept","return"].includes(o.decision))throw Error("Invalid review decision");
 if(o.decision==="accept"){
  if(!["E1","E2"].includes(f.evidenceClass)||f.contradiction==="open")throw Error("Insufficient or conflicting evidence; return for follow-up");
  if(f.evidenceStrength==="Not assessed")throw Error("Evidence strength must be assessed before acceptance");
  if(o.confirmed!==true)throw Error("Confirm relevance, direct support, independent corroboration where applicable and unresolved gaps");
 }
 const r={...o,id:id("R-",s.reviews)};s.reviews.push(r);event(s,"human review: "+o.decision,r.id,o.reviewer);return r;
}
function gates(){return {pilotScoring:false,executiveRelease:false,publicDeployment:false,reason:"Approved register integrated; final validation specification, scoring calibration, secure handling and release approval outstanding."};}
function restore(raw,criteria,requests,baseline){
 if(!raw||raw.version!=="0.1.0-rc.1"||raw.baseline!=="1.0-reconstructed-rc.1")throw Error("Unsupported snapshot version");
 if(JSON.stringify(raw.sourceManifest)!==JSON.stringify(baseline)||JSON.stringify(raw.requestCatalogue)!==JSON.stringify(requests))throw Error("Snapshot baseline mismatch");
 if(!["evidence","findings","reviews","requestEvents","events"].every(k=>Array.isArray(raw[k])))throw Error("Malformed snapshot");
 if(raw.events.length>20000)throw Error("Snapshot too large");
 const s=create();
 const lists={evidence:raw.evidence,findings:raw.findings,reviews:raw.reviews,requestEvents:raw.requestEvents};
 for(const e of raw.events){
  if(!e||e.sequence!==s.events.length+1||!Number.isFinite(Date.parse(e.time)))throw Error("Invalid event sequence");
  const find=k=>{const rows=lists[k].filter(r=>r&&r.id===e.id);if(rows.length!==1)throw Error("Invalid or duplicate record reference");return rows[0];};
  if(e.action==="scope recorded")setScope(s,raw.scope||{});
  else if(e.action==="evidence captured")addEvidence(s,find("evidence"),criteria,requests);
  else if(e.action==="finding drafted")addFinding(s,find("findings"),criteria);
  else if(e.action==="human review: accept"||e.action==="human review: return")review(s,find("reviews"));
  else if(e.action==="request requested"||e.action==="request missing")markRequest(s,find("requestEvents"),requests);
  else throw Error("Unknown event action");
  const current=s.events.at(-1);
  if(current.action!==e.action||current.id!==e.id||current.actor!==e.actor)throw Error("Event does not match replayed record");
  current.time=e.time;
 }
 if(!!s.scope!==!!raw.scope||Object.keys(lists).some(k=>s[k].length!==lists[k].length))throw Error("Orphan records in snapshot");
 return s;
}
const api={create,setScope,requestState,markRequest,criterionCoverage,addEvidence,addFinding,review,gates,restore};
if(typeof module!=="undefined")module.exports=api;else g.TCI=api;
})(globalThis);
