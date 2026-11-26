"use strict";
let s=TCI.create(); const criteria=BASELINE.criteria, requests=REQUESTS, $=id=>document.getElementById(id);
const option=(value,text)=>new Option(text,value);
const criterion=$("criterion");
requests.forEach(r=>$("request-select").add(option(r.id,r.id+" · "+r.title)));
criteria.forEach(c=>criterion.add(option(c.id,c.id+" · "+c.dimension+" / "+c.criterion)));
function line(parent,tag,text){const el=document.createElement(tag);el.textContent=text;parent.append(el);return el;}
function render(){
 const c=criteria.find(c=>c.id===criterion.value);
 $("criterion-source").textContent=c.question+" | "+c.source;
 $("scope").hidden=Boolean(s.scope);
 $("scope-summary").replaceChildren();if(s.scope){line($("scope-summary"),"strong",s.scope.title+" · "+s.scope.period);line($("scope-summary"),"p",s.scope.decision+" | "+s.scope.boundary+" | Owner: "+s.scope.owner);}
 $("request-list").replaceChildren();
 for(const r of requests){const a=line($("request-list"),"article","");line(a,"strong",r.id+" · "+r.title);line(a,"span",TCI.requestState(s,r.id));line(a,"small",r.dimension+" · "+r.source);}
 $("evidence-request").replaceChildren(option("","Ad hoc evidence / not linked"));requests.filter(r=>r.dimension===c.dimension).forEach(r=>$("evidence-request").add(option(r.id,r.id+" · "+r.title)));
 $("stats").replaceChildren();
 for(const [value,label] of [[requests.filter(r=>TCI.requestState(s,r.id)==="received").length+"/21","Legacy requests received"],[s.evidence.length,"Evidence records"],[s.findings.length,"Draft findings"],[s.reviews.filter(r=>r.decision==="accept").length,"Accepted reviews"],["Locked","Scoring"]]){
 const card=line($("stats"),"div","");card.className="stat";line(card,"strong",value);line(card,"span",label);}
 $("refs").replaceChildren();for(const e of s.evidence.filter(e=>e.criterion===c.id)){const label=line($("refs"),"label","");const inp=document.createElement("input");inp.type="checkbox";inp.value=e.id;label.append(inp,document.createTextNode(e.id+" · "+e.title));}
 if(!$("refs").children.length)line($("refs"),"p","No evidence recorded.");
 $("review-select").replaceChildren(option("","Select unreviewed finding"));s.findings.filter(f=>!s.reviews.some(r=>r.finding===f.id)).forEach(f=>$("review-select").add(option(f.id,f.id+" · "+f.claim)));
 const ledger=$("ledger");ledger.replaceChildren();
 for(const e of s.evidence){const a=line(ledger,"article","");line(a,"strong",e.id+" · "+e.criterion+" · "+e.title);line(a,"p",e.source+" | "+e.version+" | "+e.location+" | "+e.owner+" | "+e.period);line(a,"p",e.note);line(a,"small","Request: "+(e.requestId||"Ad hoc")+" | SHA-256: "+e.sha256);}
 for(const f of s.findings){const a=line(ledger,"article","");line(a,"strong",f.id+" · "+f.criterion+" · "+f.evidenceClass+" · "+f.claim);line(a,"p","Evidence: "+(f.refs.join(", ")||"None")+" | Contradiction: "+f.contradiction);line(a,"p","Gap: "+f.gap+" | Follow-up: "+f.action); if(f.contradictionDetail)line(a,"p",f.contradictionDetail+" | "+f.resolution); const r=s.reviews.find(r=>r.finding===f.id);line(a,"p",r?r.decision+" by "+r.reviewer+": "+r.reason:"Awaiting review");}
 line(ledger,"h3","Activity history");for(const e of s.events)line(ledger,"p",e.sequence+" · "+e.time+" · "+e.actor+" · "+e.action+" · "+e.id);
}
criterion.addEventListener("change",render);
const values=f=>Object.fromEntries(new FormData(f));
function bind(name,handler){$(name).addEventListener("submit",async e=>{e.preventDefault();try{await handler(e.target,values(e.target));e.target.reset();render();$("status").textContent="Recorded successfully.";}catch(err){$("status").textContent=err.message;}});}
bind("scope",(f,o)=>TCI.setScope(s,o));
bind("request",(f,o)=>TCI.markRequest(s,o,requests));
bind("evidence",async(f,o)=>{const selectedCriterion=criterion.value;const target=s;const file=o.file;if(!file||!file.size)throw Error("Select a non-empty synthetic file");if(file.size>25*1024*1024)throw Error("Synthetic file limit is 25 MB");const bytes=await file.arrayBuffer();const hash=await crypto.subtle.digest("SHA-256",bytes);if(target!==s)throw Error("Session changed; retry intake");delete o.file;TCI.addEvidence(s,{...o,criterion:selectedCriterion,filename:file.name,sha256:Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,"0")).join("")},criteria,requests);});
bind("finding",(f,o)=>TCI.addFinding(s,{...o,criterion:criterion.value,refs:[...$("refs").querySelectorAll("input:checked")].map(x=>x.value)},criteria));
bind("review",(f,o)=>TCI.review(s,{...o,confirmed:f.elements.confirmed.checked}));
$("export").addEventListener("click",()=>{const blob=new Blob([JSON.stringify({...s,sourceManifest:BASELINE,requestCatalogue:REQUESTS,gates:TCI.gates()},null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="TCI-private-draft.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});
$("restore").addEventListener("click",async()=>{try{if(s.scope||s.events.length)throw Error("Restore into a blank session only; export your work then reload");
const file=$("restore-file").files[0];if(!file||file.size>10*1024*1024)throw Error("Select a JSON snapshot under 10 MB");const raw=JSON.parse(await file.text());if(s.scope||s.events.length)throw Error("Session changed; reload before restore");s=TCI.restore(raw,criteria,requests,BASELINE);render();$("status").textContent="Restored unverified prior records; scoring and release remain locked.";}catch(e){$("status").textContent=e.message;}});render();
