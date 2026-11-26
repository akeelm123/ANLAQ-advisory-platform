const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process');
const readline=require('node:readline');
const assert=require('node:assert/strict');
const path=require('node:path');
(async()=>{
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0'],{stdio:['ignore','pipe','pipe'],env:process.env});
 const rl=readline.createInterface({input:proc.stdout});
 let browser;
 try{
  const cfg=await new Promise((resolve,reject)=>{rl.once('line',x=>{try{resolve(JSON.parse(x));}catch(e){reject(e);}});proc.once('exit',()=>reject(Error('Local synthetic server stopped')));});
  browser=await chromium.launch({channel:'chrome',headless:false});const p=await browser.newPage({viewport:{width:1280,height:1000}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
  await p.goto(cfg.url);
  async function sign(role){await p.locator('#login [name=username]').fill(role);await p.locator('#login [name=password]').fill(cfg.users[role]);await p.locator('#login button').click();await p.getByText('Signed in as '+role).waitFor();}
  async function out(){await p.locator('#logout').click();await p.locator('#login-section').waitFor({state:'visible'});}
  async function fill(form,fields){for(const [n,v] of Object.entries(fields))await p.locator('#'+form+' [name="'+n+'"]').fill(v);}
  async function waitStatus(t){await p.locator('#status').filter({hasText:t}).waitFor();}
  await sign('assessor');assert.equal(await p.locator('#catalogue article').count(),32);await p.locator('#request-id').selectOption('SA-01');await fill('request',{reason:'Synthetic evidence request'});await p.locator('#request button').click();await waitStatus('Request update recorded.');await out();
  await sign('contributor');assert.equal(await p.locator('#upload-criterion option').count(),28);await p.locator('#upload-criterion').selectOption('Q01');await p.locator('#upload-request').selectOption('SA-01');
  await fill('upload',{title:'Synthetic strategy mandate',sourceOwner:'Synthetic sponsor',period:'FY26',sourceVersion:'1',locator:'line 1'});
  await p.locator('#upload [name=file]').setInputFiles({name:'synthetic.txt',mimeType:'text/plain',buffer:Buffer.from('Synthetic strategy evidence only')});await p.locator('#upload button').click();await waitStatus('Source submitted to quarantine.');await p.getByText('Synthetic strategy mandate · v1 · quarantined').waitFor();await out();
  await sign('assessor');await p.locator('#quarantine').selectOption({index:1});await p.locator('#inspect').click();await p.locator('#quarantine-text').filter({hasText:'Synthetic strategy evidence only'}).waitFor();await fill('screen',{reason:'Synthetic manual inspection'});await p.locator('#screen button').click();await waitStatus('Disposition recorded.');await p.getByText('Synthetic strategy mandate · v1 · accepted').waitFor();
  await p.locator('#finding-criterion').selectOption('Q01');await p.locator('#finding-links input').check();await fill('finding',{claim:'Synthetic strategy linkage finding'});await p.locator('#finding [name=strength]').selectOption('Strong');await p.locator('#finding button').click();await waitStatus('Draft finding recorded.');await out();
  await sign('reviewer');await p.locator('#preview-id').selectOption({index:1});await p.locator('#preview').click();await p.locator('#accepted-text').filter({hasText:'Synthetic strategy evidence only'}).waitFor();await p.locator('#review-finding').selectOption({index:1});await p.locator('#review [name=decision]').selectOption('accept');await fill('review',{reason:'Synthetic independent review'});await p.locator('#review [name=confirmed]').check();await p.locator('#review button').click();await waitStatus('Independent review recorded.');await p.getByText('Q01 · E1 / Strong · accept').waitFor();await out();
  await sign('owner');await p.getByText('Q01 · E1 / Strong · accept').waitFor();await p.locator('#release').click();await waitStatus('Access denied or release gate locked');
  assert.deepEqual(errors,[]);
  if(process.env.TCI_SCREENSHOT)await p.screenshot({path:process.env.TCI_SCREENSHOT,fullPage:true});
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await out();assert.equal(await p.locator('#workspace').isVisible(),false);assert.equal(await p.locator('#versions article').count(),0);assert.equal(await p.locator('#findings article').count(),0);assert.equal(await p.evaluate(()=>localStorage.length+sessionStorage.length),0);
  console.log('PASS: synthetic contributor, assessor, reviewer and owner browser journey; catalogue, request, source upload, quarantine, evidence linkage, independent review, locked release, logout, mobile width; no page errors.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
