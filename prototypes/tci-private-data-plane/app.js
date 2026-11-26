"use strict";
const $=id=>document.getElementById(id), opt=(v,t)=>new Option(t,v), formValues=f=>Object.fromEntries(new FormData(f));
let token=null,assessment=null,assessments=[],view=null,busy=false,inspected=null,interviewProposal=null;
function item(parent,tag,text,cls){const e=document.createElement(tag);e.textContent=text;if(cls)e.className=cls;parent.append(e);return e;}
function status(t){$("status").textContent=t;}
async function api(path,method="GET",data=null){
 const headers={};if(token)headers.Authorization="Bearer "+token;if(data!==null)headers["Content-Type"]="application/json";
 const res=await fetch(path,{method,headers,body:data===null?undefined:JSON.stringify(data),cache:"no-store"});
 const result=await res.json();if(!res.ok)throw Error(result.error||"Request refused");return result;
}
const path=action=>"/api/assessments/"+encodeURIComponent(assessment)+"/"+action;
function fill(select,items,selected=""){select.replaceChildren(...items.map(([v,t])=>opt(v,t)));if(items.some(([v])=>v===selected))select.value=selected;}
function catalogueFor(id){return view.catalogue.requests.filter(r=>r.criteria.includes(id));}
function showUploadRequests(){const sel=$("upload-request"),before=sel.value;fill(sel,catalogueFor($("upload-criterion").value).map(r=>[r.id,r.id+" · "+r.title]),before);}
function latestVersions(){const map=new Map();for(const v of view.versions){if(!map.has(v.documentId)||map.get(v.documentId).version<v.version)map.set(v.documentId,v);}return [...map.values()];}
function showExtractionSources(){
 const selected=$("extraction-criterion").value,requests=new Set(catalogueFor(selected).map(r=>r.id));
 fill($("extraction-source"),[["","Choose accepted mapped source"],...latestVersions().filter(v=>v.status==="accepted"&&requests.has(v.requestId)).map(v=>[v.versionId,v.title+" · "+v.requestId+" · v"+v.version])]);
}
function showExtractions(){
 $("extractions").replaceChildren();
 for(const r of view.extractions){const card=item($("extractions"),"article","","record");item(card,"strong",r.criterionId+" · "+r.sourceTitle+" · "+r.state);item(card,"p",(r.result.semanticReviewRequired?r.result.counts.candidate+" candidate passages":r.result.counts.present+" present")+" · "+r.result.counts.missing+" missing · "+r.result.counts.ambiguous+" ambiguous · scoring locked");item(card,"small","Source SHA-256 "+r.sourceSha256+" · method "+r.method+(r.result.model?" · local model "+r.result.model:""));if(r.result.semanticReviewRequired)item(card,"p","Source-verified quotes only — field attribution and completeness require human review; rejected proposals: "+r.result.rejectedProposals+(r.result.retryAttempted?" · targeted retry used":"")+(r.result.explicitMaterialityFallbackUsed?" · explicit materiality statement recovered":""));
 const details=document.createElement("details");card.append(details);item(details,"summary","Review field values and source citations");for(const f of r.result.fields){const block=item(details,"div","","record");item(block,"strong",f.label+" · "+f.status);if(f.value!==null)item(block,"p",f.value);for(const c of (f.absenceCitations||[]))item(block,"p","Source explicitly reports unavailable: "+c.location+" — "+c.value);for(const c of f.citations)item(block,"p",(c.location||"Line "+c.line)+(c.startColumn?", columns "+c.startColumn+"–"+c.endColumn:"")+": "+c.excerpt);}
 }
 fill($("extraction-run"),[["","Choose draft extraction"],...view.extractions.filter(r=>r.state==="draft").map(r=>[r.id,r.criterionId+" · "+r.sourceTitle])]);
}
function showFindingLinks(){const root=$("finding-links");root.replaceChildren();const selected=$("finding-criterion").value,requests=new Set(catalogueFor(selected).map(r=>r.id));for(const v of latestVersions().filter(v=>v.status==="accepted"&&v.requestId&&requests.has(v.requestId))){
 const label=item(root,"label","","check"),check=document.createElement("input");check.type="checkbox";check.value=v.versionId;label.append(check,document.createTextNode(v.title+" · "+v.requestId+" · "+v.locator+" · v"+v.version));}
 if(!root.children.length)item(root,"p","No accepted mapped source version.");
}
function interviewLinks(){
 const target=$("interview-links");target.replaceChildren();if(!view.interviews)return;
 const q=view.interviews.questions.find(q=>q.questionId===$("interview-question").value);
 if(!q)return;$("interview-question-text").textContent=q.question+" | "+q.suggestedStakeholder;
 const requests=new Set([...q.primaryRequests,...q.supplementaryRequests,...q.conditionalRequests]);
 for(const v of latestVersions().filter(v=>v.status==="accepted"&&requests.has(v.requestId))){const label=item(target,"label","","check");const c=document.createElement("input");c.type="checkbox";c.value=v.versionId;label.append(c,document.createTextNode(v.title+" · "+v.requestId+" · "+v.locator));}
 if(!target.children.length)item(target,"p","No accepted current mapped source. Response remains an assertion.");
}
function interviewChoice(){
 const c=view.interviews?.claims.find(c=>c.id===$("followup-claim").value),s=c?.suggestion;interviewProposal=null;$("interview-ai-note").textContent="";$("interview-ai-wording").hidden=!(view.narrativeEnabled&&view.role==="assessor"&&s?.triggerId&&!s?.openFollowUpId&&c?.responseStatus==="answered");
 $("followup-question").value=s?.question||"";$("followup-reason").textContent=s?.openFollowUpId?"An open follow-up already exists. Capture the answer first.":s?.triggerId?s.triggerId+" · "+s.reason+" · unresolved: "+s.unresolvedTriggers.join(", "):"All suggested triggers addressed; underlying gaps still require review.";
 $("followup-submit").disabled=!s?.triggerId||Boolean(s?.openFollowUpId);
}
function renderInterviews(){
 const i=view.interviews,role=view.role;$("interviews-section").hidden=!i;if(!i){for(const id of ["interview-summary","interview-links","interview-claims","interview-conflicts","interview-session","interview-question","conflict-a","conflict-b","followup-claim","open-followup","interview-review-claim"])$(id).replaceChildren();$("interview-question-text").textContent="";$("followup-reason").textContent="";$("followup-question").value="";return;}
 for(const id of ["interview-start-section","interview-response-section","interview-conflict-section","interview-followup-section"])$(id).hidden=role!=="assessor";
 $("interview-review-section").hidden=role!=="reviewer";
 $("interview-summary").replaceChildren();for(const [value,label] of [[i.questions.length,"Approved questions"],[i.sessions.length,"Synthetic sessions"],[i.claims.length,"Unverified claims"],[i.conflicts.length,"Open contradictions"]]){const s=item($("interview-summary"),"div","","stat");item(s,"strong",value);item(s,"span",label);}
 fill($("interview-session"),[["","Choose session"],...i.sessions.map(s=>[s.id,s.persona+" · "+s.stakeholderRef])],$("interview-session").value);
 fill($("interview-question"),i.questions.map(q=>[q.questionId,q.questionId+" · "+q.dimension+" / "+q.criterion]),$("interview-question").value);interviewLinks();
 const claims=i.claims.map(c=>[c.id,c.questionId+" · "+c.persona+" · "+(c.verbatim||c.responseStatus).slice(0,60)]);
 fill($("conflict-a"),[["","Select claim"],...claims]);fill($("conflict-b"),[["","Select another claim"],...claims]);
 fill($("followup-claim"),[["","Select claim"],...claims],$("followup-claim").value);interviewChoice();
 fill($("open-followup"),[["","Choose open follow-up"],...i.claims.flatMap(c=>c.followUps.filter(f=>!f.answer).map(f=>[f.id,c.questionId+" · "+c.persona+" · "+f.trigger_id]))]);
 fill($("interview-review-claim"),[["","Choose unreviewed claim"],...i.claims.filter(c=>!c.captureReview).map(c=>[c.id,c.questionId+" · "+c.persona])]);
 $("interview-claims").replaceChildren();for(const c of i.claims){const a=item($("interview-claims"),"article","","record");item(a,"strong",c.questionId+" · "+c.persona+" · "+c.claimClass+" · "+c.responseStatus);item(a,"p","Verbatim: "+(c.verbatim||"(no response)"));item(a,"p","Assessor interpretation: "+c.interpretation);item(a,"p","Unresolved triggers: "+c.suggestion.unresolvedTriggers.join(", ")+" · unverified claim");if(c.links.length)item(a,"p",c.links.map(l=>l.requestId+" / "+l.locator+(l.current?"":" (superseded)")).join("; "));if(c.captureReview)item(a,"p","Capture review: "+c.captureReview.decision+" — "+c.captureReview.reason);for(const f of c.followUps){item(a,"p","Follow-up "+f.trigger_id+": "+f.question+" · "+(f.answer?f.answer.status+" — "+f.answer.verbatim:"open")+(f.modelProposal?" · local model wording reviewed":""))}}
 $("interview-conflicts").replaceChildren();for(const c of i.conflicts){const a=item($("interview-conflicts"),"article","","record");const names=[c.claimA,c.claimB].map(id=>i.claims.find(x=>x.id===id)?.persona||id);item(a,"strong","Open contradiction · "+names.join(" vs "));item(a,"p",c.topic+" · "+(c.material?"decision-material":"non-material")+" · independent reconciliation required");}
}
function render(){
 const role=view.role, a=assessments.find(a=>a.id===assessment);
 $("role").textContent="Signed in as "+role;$("assessment-title").textContent=a.title;$("assessment-scope").textContent=a.scope;
 $("request").hidden=role!=="assessor";$("upload-section").hidden=!["assessor","contributor"].includes(role);
 $("screen-section").hidden=role!=="assessor";$("finding-section").hidden=role!=="assessor";$("findings-section").hidden=role==="contributor";$("review").hidden=role!=="reviewer";$("release").hidden=role!=="owner";$("extraction-section").hidden=role==="contributor";$("extract").hidden=role!=="assessor";$("extraction-review").hidden=role!=="reviewer";
 $("coverage-note").textContent=view.catalogue.coverageVisibility+" · Receipt is not evidence sufficiency or validation.";
 $("stats").replaceChildren();for(const [value,label] of [[view.catalogue.requests.filter(r=>r.status==="received").length+"/"+view.catalogue.catalogueCount,"Requests received"],[view.versions.length,"Source versions"],[view.findings.length,"Visible findings"],["Locked","Release"]]){const s=item($("stats"),"div","","stat");item(s,"strong",value);item(s,"span",label);}
 $("catalogue").replaceChildren();for(const r of view.catalogue.requests){const a=item($("catalogue"),"article","");item(a,"strong",r.id+" · "+r.title);item(a,"span",r.status);item(a,"small",r.dimension);}
 fill($("request-id"),view.catalogue.requests.map(r=>[r.id,r.id+" · "+r.title]),$("request-id").value);
 const cs=view.catalogue.criteria.map(c=>[c.id,c.id+" · "+c.dimension+" / "+c.criterion]);
 fill($("upload-criterion"),cs,$("upload-criterion").value);showUploadRequests();
 fill($("finding-criterion"),cs,$("finding-criterion").value);showFindingLinks();fill($("extraction-criterion"),cs,$("extraction-criterion").value);showExtractionSources();fill($("extraction-mode"),[["labelled","Labelled fields (deterministic)"],...(view.narrativeEnabled?[["narrative","Narrative passages (local model, synthetic only)"]]:[])]);showExtractions();
 fill($("replacement"),[["","Create new document"],...latestVersions().filter(v=>role!=="contributor"||v.own).map(v=>[v.documentId,v.title])]);
 fill($("quarantine"),[["","Choose quarantined source"],...view.versions.filter(v=>v.status==="quarantined"&&!v.own).map(v=>[v.versionId,v.title+" · v"+v.version])]);inspected=null;$("quarantine-text").textContent="";
 fill($("preview-id"),[["","Choose accepted source"],...view.versions.filter(v=>v.status==="accepted").map(v=>[v.versionId,v.title+" · v"+v.version])]);$("accepted-text").textContent="";
 $("versions").replaceChildren();for(const v of view.versions){const a=item($("versions"),"article","","record");item(a,"strong",v.title+" · v"+v.version+" · "+v.status);item(a,"p",(v.requestId||"Unlinked")+" · "+(v.criterion||"")+" · "+(v.sourceOwner||"")+" · "+(v.period||"")+" · "+(v.locator||""));item(a,"small","SHA-256 "+v.sha256);}
 $("findings").replaceChildren();for(const f of view.findings){const a=item($("findings"),"article","","record");item(a,"strong",f.criterion+" · "+f.evidenceClass+" / "+f.strength+" · "+f.state);item(a,"p",f.claim);item(a,"p",f.links.map(l=>l.requestId+" / "+l.locator).join("; "));}
 fill($("review-finding"),[["","Choose draft finding"],...view.findings.filter(f=>f.state==="draft").map(f=>[f.id,f.criterion+" · "+f.claim])]);renderInterviews();
}
async function refresh(){view=await api(path("dashboard"));render();}
async function run(fn){if(busy)return;busy=true;try{await fn();}catch(e){status(e.message);}finally{busy=false;}}
function bind(id,fn){$(id).addEventListener("submit",e=>{e.preventDefault();run(async()=>{await fn(formValues(e.target),e.target);});});}
bind("login",async(o,f)=>{const r=await api("/api/login","POST",o);token=r.token;try{assessments=(await api("/api/assessments")).assessments;if(!assessments.length)throw Error("No authorised assessment");assessment=assessments[0].id;fill($("assessment"),assessments.map(a=>[a.id,a.title]));await refresh();f.reset();$("login-section").hidden=true;$("workspace").hidden=false;status("Signed in.");}catch(e){token=null;throw e;}});
$("logout").addEventListener("click",()=>run(async()=>{try{await api("/api/logout","POST",{});}finally{token=null;assessment=null;view=null;assessments=[];interviewProposal=null;$("workspace").hidden=true;$("login-section").hidden=false;$("workspace").querySelectorAll("form").forEach(f=>f.reset());for(const id of ["stats","catalogue","versions","finding-links","findings","extractions","interview-summary","interview-links","interview-claims","interview-conflicts","interview-session","interview-question","conflict-a","conflict-b","followup-claim","open-followup","interview-review-claim","extraction-criterion","extraction-source","extraction-run","assessment","request-id","upload-criterion","upload-request","replacement","quarantine","preview-id","finding-criterion","review-finding"])$(id).replaceChildren();for(const id of ["role","assessment-title","assessment-scope","coverage-note","quarantine-text","accepted-text","interview-question-text","followup-reason","interview-ai-note"])$(id).textContent="";status("Signed out.");}}));
$("assessment").addEventListener("change",()=>run(async()=>{assessment=$("assessment").value;await refresh();}));
$("upload-criterion").addEventListener("change",showUploadRequests);$("finding-criterion").addEventListener("change",showFindingLinks);$("extraction-criterion").addEventListener("change",showExtractionSources);
bind("request",async(o,f)=>{await api(path("request"),"POST",o);f.reset();await refresh();status("Request update recorded.");});
bind("upload",async(o,f)=>{const file=o.file;if(!file||file.size<1||file.size>256*1024)throw Error("Synthetic document must be 1–262144 bytes");const bytes=new Uint8Array(await file.arrayBuffer());let raw="";for(const b of bytes)raw+=String.fromCharCode(b);
 await api(path("upload"),"POST",{title:o.title,filename:file.name,documentId:o.documentId,contentBase64:btoa(raw),intake:{criterion:o.criterion,requestId:o.requestId,sourceOwner:o.sourceOwner,period:o.period,sourceVersion:o.sourceVersion,locator:o.locator}});f.reset();await refresh();status("Source submitted to quarantine.");});
$("quarantine").addEventListener("change",()=>{inspected=null;$("quarantine-text").textContent="";});
$("inspect").addEventListener("click",()=>run(async()=>{const id=$("quarantine").value;if(!id)throw Error("Choose a quarantined source");const r=await api(path("inspect"),"POST",{versionId:id});inspected=id;$("quarantine-text").textContent=r.text;status("Synthetic quarantine content inspected.");}));
bind("screen",async(o,f)=>{const id=$("quarantine").value;if(!id||inspected!==id)throw Error("Inspect the selected source first");await api(path("screen"),"POST",{...o,versionId:id});f.reset();await refresh();status("Disposition recorded.");});
$("preview").addEventListener("click",()=>run(async()=>{const id=$("preview-id").value;if(!id)throw Error("Choose accepted source");const r=await api(path("preview"),"POST",{versionId:id});$("accepted-text").textContent=r.text;status("Accepted source previewed.");}));
bind("extract",async(o,f)=>{if(o.mode==="narrative")status("Local model proposing source passages; this can take a minute.");await api(path("extract"),"POST",o);f.reset();await refresh();status("Draft extraction recorded.");});
bind("extraction-review",async(o,f)=>{await api(path("extraction-review"),"POST",{...o,confirmed:f.elements.confirmed.checked});f.reset();await refresh();status("Independent extraction review recorded.");});
bind("finding",async(o,f)=>{const links=[...$("finding-links").querySelectorAll("input:checked")].map(input=>{const v=view.versions.find(v=>v.versionId===input.value);return{versionId:v.versionId,requestId:v.requestId,locator:v.locator};});await api(path("finding"),"POST",{criterion:o.criterion,claim:o.claim,evidenceClass:o.evidenceClass,strength:o.strength,contradiction:f.elements.contradiction.checked,links});f.reset();await refresh();status("Draft finding recorded.");});
bind("review",async(o,f)=>{await api(path("review"),"POST",{...o,confirmed:f.elements.confirmed.checked});f.reset();await refresh();status("Independent review recorded.");});
$("release").addEventListener("click",()=>run(async()=>{await api(path("release"),"POST",{});status("Unexpected release result.");}));

$("interview-question").addEventListener("change",interviewLinks);$("followup-claim").addEventListener("change",interviewChoice);
bind("interview-start",async(o,f)=>{await api(path("interview-start"),"POST",o);f.reset();await refresh();status("Synthetic interview session started.");});
bind("interview-response",async(o,f)=>{const links=[...$("interview-links").querySelectorAll("input:checked")].map(x=>{const v=view.versions.find(v=>v.versionId===x.value);return{versionId:v.versionId,requestId:v.requestId,locator:v.locator};});const flags=[...f.querySelectorAll('[name="flags"]:checked')].map(x=>x.value);await api(path("interview-response"),"POST",{sessionId:o.sessionId,questionId:o.questionId,status:o.status,verbatim:o.verbatim,interpretation:o.interpretation,flags,links});f.reset();await refresh();status("Interview response and draft claim recorded.");});
bind("interview-conflict",async(o,f)=>{await api(path("interview-conflict"),"POST",{...o,material:f.elements.material.checked});f.reset();await refresh();status("Open contradiction recorded.");});
bind("interview-followup",async(o,f)=>{const s=view.interviews.claims.find(c=>c.id===o.claimId)?.suggestion;if(!s?.triggerId)throw Error("Choose a current proposed follow-up");await api(path("interview-followup"),"POST",{...o,triggerId:s.triggerId,proposalId:interviewProposal?.proposalId||null});f.reset();await refresh();status("Human-confirmed follow-up recorded.");});
bind("interview-answer",async(o,f)=>{await api(path("interview-answer"),"POST",o);f.reset();await refresh();status("Follow-up answer recorded; review still required.");});
bind("interview-review",async(o,f)=>{await api(path("interview-review"),"POST",{...o,confirmed:f.elements.confirmed.checked});f.reset();await refresh();status("Independent capture review recorded.");});

$("interview-ai-wording").addEventListener("click",()=>run(async()=>{const claimId=$("followup-claim").value;if(!claimId)throw Error("Choose a claim");status("Local model proposing wording for this approved trigger.");const r=await api(path("interview-model-wording"),"POST",{claimId});if($("followup-claim").value!==claimId)throw Error("Claim changed; select again");interviewProposal=r;$("followup-question").value=r.question;$("interview-ai-note").textContent="Draft only · "+r.model+" · source quote: "+r.quote+" · verify wording before recording.";status("Local model wording ready for human review; no follow-up recorded.");}));
