"use strict";
const s=TCI.create(), criteria=BASELINE.criteria, $=id=>document.getElementById(id);
const option=(value,text)=>new Option(text,value);
const criterion=$("criterion");
criteria.forEach(c=>criterion.add(option(c.id,c.id+" · "+c.dimension+" / "+c.criterion)));
function line(parent,tag,text){const el=document.createElement(tag);el.textContent=text;parent.append(el);return el;}
function render(){
 const c=criteria.find(c=>c.id===criterion.value);
 $("criterion-source").textContent=c.question+" | "+c.source;
 $("stats").replaceChildren();
 for(const [value,label] of [[s.evidence.length,"Evidence records"],[s.findings.length,"Draft findings"],[s.reviews.filter(r=>r.decision==="accept").length,"Accepted reviews"],["Locked","Scoring"]]){
 const card=line($("stats"),"div","");card.className="stat";line(card,"strong",value);line(card,"span",label);}
 $("refs").replaceChildren();for(const e of s.evidence.filter(e=>e.criterion===c.id)){const label=line($("refs"),"label","");const inp=document.createElement("input");inp.type="checkbox";inp.value=e.id;label.append(inp,document.createTextNode(e.id+" · "+e.title));}
 if(!$("refs").children.length)line($("refs"),"p","No evidence recorded.");
 $("review-select").replaceChildren(option("","Select unreviewed finding"));s.findings.filter(f=>!s.reviews.some(r=>r.finding===f.id)).forEach(f=>$("review-select").add(option(f.id,f.id+" · "+f.claim)));
 const ledger=$("ledger");ledger.replaceChildren();
 for(const e of s.evidence){const a=line(ledger,"article","");line(a,"strong",e.id+" · "+e.criterion+" · "+e.title);line(a,"p",e.source+" | "+e.version+" | "+e.location+" | "+e.owner+" | "+e.period);line(a,"p",e.note);line(a,"small","SHA-256: "+e.sha256);}
 for(const f of s.findings){const a=line(ledger,"article","");line(a,"strong",f.id+" · "+f.criterion+" · "+f.evidenceClass+" · "+f.claim);line(a,"p","Evidence: "+(f.refs.join(", ")||"None")+" | Contradiction: "+f.contradiction);line(a,"p","Gap: "+f.gap+" | Follow-up: "+f.action); if(f.contradictionDetail)line(a,"p",f.contradictionDetail+" | "+f.resolution); const r=s.reviews.find(r=>r.finding===f.id);line(a,"p",r?r.decision+" by "+r.reviewer+": "+r.reason:"Awaiting review");}
 line(ledger,"h3","Activity history");for(const e of s.events)line(ledger,"p",e.sequence+" · "+e.time+" · "+e.actor+" · "+e.action+" · "+e.id);
}
criterion.addEventListener("change",render);
const values=f=>Object.fromEntries(new FormData(f));
function bind(name,handler){$(name).addEventListener("submit",async e=>{e.preventDefault();try{await handler(e.target,values(e.target));e.target.reset();render();$("status").textContent="Recorded successfully.";}catch(err){$("status").textContent=err.message;}});}
bind("evidence",async(f,o)=>{const selectedCriterion=criterion.value;const file=o.file;if(!file||!file.size)throw Error("Select a non-empty synthetic file");const bytes=await file.arrayBuffer();const hash=await crypto.subtle.digest("SHA-256",bytes);delete o.file;TCI.addEvidence(s,{...o,criterion:selectedCriterion,filename:file.name,sha256:Array.from(new Uint8Array(hash),b=>b.toString(16).padStart(2,"0")).join("")},criteria);});
bind("finding",(f,o)=>TCI.addFinding(s,{...o,criterion:criterion.value,refs:[...$("refs").querySelectorAll("input:checked")].map(x=>x.value)},criteria));
bind("review",(f,o)=>TCI.review(s,{...o,confirmed:f.elements.confirmed.checked}));
$("export").addEventListener("click",()=>{const blob=new Blob([JSON.stringify({...s,sourceManifest:BASELINE,gates:TCI.gates()},null,2)],{type:"application/json"});const a=document.createElement("a");a.href=URL.createObjectURL(blob);a.download="TCI-private-draft.json";a.click();setTimeout(()=>URL.revokeObjectURL(a.href),1000);});render();
