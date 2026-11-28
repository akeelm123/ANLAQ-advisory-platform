const {chromium}=require(process.env.PLAYWRIGHT_MODULE||"playwright");
const {spawn}=require("child_process"),readline=require("readline"),assert=require("assert/strict"),path=require("path"),fs=require("fs");
(async()=>{let server,browser;try{
 server=spawn(process.env.TCI_PYTHON||"python3",[path.join(__dirname,"simple_preview.py"),"--port","8774","--dashboard"],{stdio:["ignore","pipe","pipe"],env:process.env});
 const ready=await new Promise((resolve,reject)=>{readline.createInterface({input:server.stdout}).once("line",l=>resolve(JSON.parse(l)));server.once("exit",()=>reject(Error("Server exit")));});
 browser=await chromium.launch({channel:"chrome",headless:true});const p=await browser.newPage({viewport:{width:1440,height:900}});const errors=[];p.on("pageerror",e=>errors.push(e.message));await p.goto(ready.url);
 const login=async()=>{await p.locator("#loginform").getByLabel("Username").fill(ready.username);await p.locator("#loginform").getByLabel("Password").fill(ready.password);await p.locator("#loginform").getByRole("button",{name:"Sign in"}).click();await p.getByText("Production release locked").waitFor();};await login();
 await p.getByRole("button",{name:"Load fictional UAT example"}).click();await p.getByText("Fictional example loaded.",{exact:false}).waitFor();await p.getByText("28 / 28",{exact:true}).first().waitFor();
 // Scripted UAT assessment inputs only. Never presented as human or model validation.
 async function api(route,body,token){const headers={"Content-Type":"application/json","Origin":ready.url};if(token)headers.Authorization="Bearer "+token;const r=await fetch(ready.url+"/api/"+route,{method:body===undefined?"GET":"POST",headers,body:body===undefined?undefined:JSON.stringify(body)});assert.ok(r.ok,await r.clone().text());return r.json();}
 const token=(await api("login",{username:ready.username,password:ready.password})).token,m=await api("methodology",undefined,token),w=await api("workspace",undefined,token),a=await api("analyze",undefined,token);
 assert.equal(a.files.length,28);assert.equal(Object.keys(w.answers).length,28);assert.equal(a.criteria.filter(c=>c.sources.length).length,28);
 const rows=Object.fromEntries(m.criteria.map(c=>[c.id,{score:3,confirmed:true,conflict:false,operating:false,sourceIds:["1"],rationale:"Scripted fictional browser UAT anchor; no independent approval"}]));
 const result=await api("calculate",{rows,interviews:w.answers},token);assert.equal(result.draftScore,3);assert.equal(result.reviewed,28);assert.equal(result.productionLocked,true);assert.equal(result.actionPlan.filter(x=>x.horizon===90).length,7);
 await api("workspace",{answers:w.answers,reviews:rows,edits:{},title:"Scripted fictional UAT scorecard",persona:"Canonical TCI"},token);
 await p.reload();await login();await p.locator("#dashboard-kpis").getByText("3.00 / 5",{exact:true}).waitFor();await p.locator("nav").getByRole("button",{name:"Summary",exact:true}).click();await p.getByRole("img",{name:"Reviewed draft seven-dimensional 1–5 confidence profile"}).waitFor();await p.getByText("Scripted fictional UAT scorecard",{exact:true}).waitFor();await p.locator("#target").selectOption("4");await p.getByText("Target 4 / 5 · target minus actual: 1.00 (reviewed draft)",{exact:true}).waitFor();await p.getByRole("heading",{name:"Proposed action plan"}).waitFor();
 if(process.env.TCI_SCREENSHOT)await p.screenshot({path:process.env.TCI_SCREENSHOT,fullPage:true});
 if(process.env.TCI_PDF){await p.pdf({path:process.env.TCI_PDF,format:"A4",printBackground:true});assert.ok(fs.statSync(process.env.TCI_PDF).size>10000);}
 await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);assert.deepEqual(errors,[]);
 console.log("PASS: 28-document fictional example, 28 interview entries, complete scripted exact weighted draft 3.00/5, seven 90-day plans, radar profile, PDF export render and mobile. No human approval or production scoring.");
 }finally{if(browser)await browser.close();if(server)server.kill();}})().catch(e=>{console.error(e);process.exit(1)});
