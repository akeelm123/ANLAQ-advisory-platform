(function(g){
"use strict";
const str = v => typeof v === "string" ? v.trim() : "";
const required = (o,ks) => {for(const k of ks) if(!str(o[k])) throw Error(k+" is required");};
const norm = v => str(v).toLowerCase();
const create = () => ({version:"0.1.0-alpha",baseline:"provisional",evidence:[],findings:[],reviews:[],events:[]});
const event = (s,action,id,actor) => s.events.push({sequence:s.events.length+1,time:new Date().toISOString(),action,id,actor});
const id = (prefix,list) => prefix+String(list.length+1).padStart(3,"0");
function addEvidence(s,o,criteria){
 required(o,["criterion","title","source","version","location","owner","period","note","actor","sha256"]);
 if(!criteria.some(c=>c.id===o.criterion)) throw Error("Unknown criterion");
 if(!/^[a-f0-9]{64}$/.test(o.sha256)) throw Error("Invalid source digest");
 const r={...o,id:id("EV-",s.evidence)}; s.evidence.push(r);event(s,"evidence captured",r.id,o.actor);return r;
}
function addFinding(s,o,criteria){
 required(o,["criterion","claim","evidenceClass","author","gap","contradiction","action"]);
 if(!criteria.some(c=>c.id===o.criterion))throw Error("Unknown criterion");
 if(!["E1","E2","E3","E4"].includes(o.evidenceClass))throw Error("Unknown evidence class");
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
 required(o,["finding","reviewer","decision","reason"]);
 const f=s.findings.find(f=>f.id===o.finding);
 if(!f)throw Error("Unknown finding");
 if(norm(f.author)===norm(o.reviewer))throw Error("A different named reviewer is required");
 if(s.reviews.some(r=>r.finding===f.id))throw Error("Already reviewed; create a new finding for reassessment");
 if(!["accept","return"].includes(o.decision))throw Error("Invalid review decision");
 if(o.decision==="accept"){
  if(!["E1","E2"].includes(f.evidenceClass)||f.contradiction==="open")throw Error("Insufficient or conflicting evidence; return for follow-up");
  if(o.confirmed!==true)throw Error("Confirm relevance, direct support, independent corroboration where applicable and unresolved gaps");
 }
 const r={...o,id:id("R-",s.reviews)};s.reviews.push(r);event(s,"human review: "+o.decision,r.id,o.reviewer);return r;
}
function gates(){return {pilotScoring:false,executiveRelease:false,publicDeployment:false,reason:"Approved register file and validation specification not verified; scoring calibration and release approval outstanding."};}
const api={create,addEvidence,addFinding,review,gates};
if(typeof module!=="undefined")module.exports=api;else g.TCI=api;
})(globalThis);
