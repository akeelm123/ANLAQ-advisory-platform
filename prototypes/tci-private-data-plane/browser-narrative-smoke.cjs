const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process');const readline=require('node:readline');const assert=require('node:assert/strict');const path=require('node:path');
const fixture=require('./narrative-fixtures.json').fixtures[0];
(async()=>{
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0','--enable-local-model'],{stdio:['ignore','pipe','pipe'],env:process.env});
 const rl=readline.createInterface({input:proc.stdout});let browser;
 try{
  const cfg=await new Promise((resolve,reject)=>{rl.once('line',x=>{try{resolve(JSON.parse(x));}catch(e){reject(e);}});proc.once('exit',()=>reject(Error('Synthetic server stopped')));});
  browser=await chromium.launch({channel:'chrome',headless:false});const p=await browser.newPage({viewport:{width:1280,height:900}});p.setDefaultTimeout(180000);const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto(cfg.url);
  const fill=async(form,fields)=>{for(const [n,v] of Object.entries(fields))await p.locator('#'+form+' [name="'+n+'"]').fill(v);};
  const sign=async(role)=>{await fill('login',{username:role,password:cfg.users[role]});await p.locator('#login button').click();await p.getByText('Signed in as '+role).waitFor();};
  const out=async()=>{await p.locator('#logout').click();await p.locator('#login-section').waitFor({state:'visible'});};
  const waitStatus=async(t)=>p.locator('#status').filter({hasText:t}).waitFor();
  await sign('contributor');await p.locator('#upload-criterion').selectOption(fixture.criterionId);await p.locator('#upload-request').selectOption(fixture.requestId);
  await fill('upload',{title:'Fictional investment paper',sourceOwner:'Synthetic committee',period:'FY26',sourceVersion:'1',locator:'line 1'});
  await p.locator('#upload [name=file]').setInputFiles({name:fixture.filename,mimeType:'text/plain',buffer:Buffer.from(fixture.text)});await p.locator('#upload button').click();await waitStatus('Source submitted to quarantine.');await out();
  await sign('assessor');await p.locator('#quarantine').selectOption({index:1});await p.locator('#inspect').click();await p.locator('#quarantine-text').filter({hasText:'Fictional investment committee paper'}).waitFor();await fill('screen',{reason:'Synthetic manual inspection'});await p.locator('#screen button').click();await waitStatus('Disposition recorded.');
  await p.locator('#extraction-criterion').selectOption(fixture.criterionId);await p.locator('#extraction-source').selectOption({index:1});await p.locator('#extraction-mode').selectOption('narrative');await p.locator('#extract button').click();await waitStatus('Draft extraction recorded.');
  await p.getByText('7 candidate passages · 0 missing · 0 ambiguous · scoring locked').waitFor();await p.locator('#extractions summary').click();await p.getByText(/Source-verified quotes only/).waitFor();assert.match(await p.locator('#extractions').textContent(),/SGD 120000/);await out();
  await sign('reviewer');await p.locator('#preview-id').selectOption({index:1});await p.locator('#preview').click();await p.locator('#accepted-text').filter({hasText:'SGD 120000'}).waitFor();await p.locator('#extraction-run').selectOption({index:1});await p.locator('#extraction-review [name=decision]').selectOption('accept');await fill('extraction-review',{reason:'Synthetic source and field context reviewed'});await p.locator('#extraction-review [name=confirmed]').check();await p.locator('#extraction-review button').click();await waitStatus('Independent extraction review recorded.');await p.getByText('Q02 · Fictional investment paper · accept').waitFor();await out();
  await sign('owner');await p.getByText('Q02 · Fictional investment paper · accept').waitFor();await p.locator('#release').click();await waitStatus('Access denied or release gate locked');assert.deepEqual(errors,[]);await out();
  console.log('PASS: live local-model synthetic narrative browser journey; seven candidate fields, exact source excerpts, independent review and locked release.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
