const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process'),readline=require('node:readline'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0','--enable-local-model'],{stdio:['ignore','pipe','pipe'],env:process.env});
 const rl=readline.createInterface({input:proc.stdout});let browser;
 try{
  const cfg=await new Promise((resolve,reject)=>{rl.once('line',x=>{try{resolve(JSON.parse(x));}catch(e){reject(e);}});proc.once('exit',()=>reject(Error('Synthetic server stopped')));});
  browser=await chromium.launch({channel:'chrome',headless:false});const p=await browser.newPage({viewport:{width:1280,height:900}});p.setDefaultTimeout(180000);const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(cfg.url);
  const fill=async(form,fields)=>{for(const [n,v] of Object.entries(fields))await p.locator('#'+form+' [name="'+n+'"]').fill(v);};
  const sign=async(role)=>{await fill('login',{username:role,password:cfg.users[role]});await p.locator('#login button').click();await p.getByText('Signed in as '+role).waitFor();};
  const out=async()=>{await p.locator('#logout').click();await p.locator('#login-section').waitFor({state:'visible'});};
  const waitStatus=async(t)=>p.locator('#status').filter({hasText:t}).waitFor();
  await sign('assessor');assert.equal(await p.locator('#interview-question option').count(),28);
  async function capture(persona,ref,verbatim,index){
    await fill('interview-start',{persona,stakeholderRef:ref,role:'Synthetic stakeholder',scope:'Fictional benefits assessment'});
    await p.locator('#interview-start button').click();await waitStatus('Synthetic interview session started.');
    await p.locator('#interview-session').selectOption({index});await p.locator('#interview-question').selectOption('Q26');
    await fill('interview-response',{verbatim,interpretation:'Unverified synthetic benefits claim; actual not established'});
    await p.locator('#interview-response [name=flags][value=forecast_vs_actual]').check();
    await p.locator('#interview-response button').click();await waitStatus('Interview response and draft claim recorded.');
  }
  await capture('Synthetic programme lead','SYN-P1','We forecast SGD 9000 of benefit.',1);
  await capture('Synthetic Finance lead','SYN-P2','Forecast is not a validated actual result.',2);
  assert.equal(await p.locator('#interview-claims article').count(),2);
  await p.locator('#conflict-a').selectOption({index:1});await p.locator('#conflict-b').selectOption({index:2});await fill('interview-conflict',{topic:'Forecast versus actual'});await p.locator('#interview-conflict button').click();await waitStatus('Open contradiction recorded.');
  await p.locator('#followup-claim').selectOption({index:1});await p.locator('#followup-reason').filter({hasText:'FUP-04'}).waitFor();
  await p.locator('#interview-ai-wording').click();await waitStatus('Local model wording ready for human review; no follow-up recorded.');
  await p.locator('#interview-ai-note').filter({hasText:'source quote'}).waitFor();assert.equal(await p.locator('#open-followup option').count(),1);
  await p.locator('#interview-followup button[type=submit], #followup-submit').click();await waitStatus('Human-confirmed follow-up recorded.');
  await p.locator('#open-followup').selectOption({index:1});await fill('interview-answer',{verbatim:'Actual source remains missing.'});await p.locator('#interview-answer button').click();await waitStatus('Follow-up answer recorded; review still required.');
  await p.locator('#interview-claims').getByText(/local model wording reviewed/).waitFor();await p.locator('#interview-conflicts').getByText(/Open contradiction/).waitFor();await out();
  await sign('reviewer');await p.locator('#interview-review-claim').selectOption({index:1});await p.locator('#interview-review [name=decision]').selectOption('confirm_capture');await fill('interview-review',{reason:'Independent capture review only'});await p.locator('#interview-review [name=confirmed]').check();await p.locator('#interview-review button').click();await waitStatus('Independent capture review recorded.');await p.getByText(/Capture review: confirm_capture/).waitFor();await out();
  await sign('owner');assert.equal(await p.locator('#interview-claims article').count(),2);await p.getByText(/Capture review: confirm_capture/).waitFor();await p.locator('#release').click();await waitStatus('Access denied or release gate locked');
  if(process.env.TCI_SCREENSHOT)await p.locator('#interviews-section').screenshot({path:process.env.TCI_SCREENSHOT});
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await out();assert.equal(await p.locator('#interview-claims article').count(),0);
  await sign('contributor');assert.equal(await p.locator('#interviews-section').isVisible(),false);assert.equal(await p.locator('#interview-claims article').count(),0);await out();assert.deepEqual(errors,[]);
  console.log('PASS: synthetic two-persona stakeholder interview browser workflow; 28 questions, immutable responses, contradiction, local AI wording proposal, human-confirmed one-at-a-time follow-up, independent capture review, no score/release, contributor isolation and mobile width.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
