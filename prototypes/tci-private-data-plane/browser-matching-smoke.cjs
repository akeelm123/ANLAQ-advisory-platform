const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process'),readline=require('node:readline'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0'],{stdio:['ignore','pipe','pipe'],env:process.env});
 const rl=readline.createInterface({input:proc.stdout});let browser;
 try{
  const cfg=await new Promise((resolve,reject)=>{rl.once('line',x=>{try{resolve(JSON.parse(x));}catch(e){reject(e);}});proc.once('exit',()=>reject(Error('Server stopped')));});
  browser=await chromium.launch({channel:'chrome',headless:true});const p=await browser.newPage({viewport:{width:1280,height:900}});p.setDefaultTimeout(15000);const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(cfg.url);
  const fill=async(form,fields)=>{for(const [n,v] of Object.entries(fields))await p.locator('#'+form+' [name="'+n+'"]').fill(v);};
  const sign=async(role)=>{await fill('login',{username:role,password:cfg.users[role]});await p.locator('#login button').click();await p.getByText('Signed in as '+role).waitFor();};
  const out=async()=>{await p.locator('#logout').click();await p.locator('#login-section').waitFor({state:'visible'});};
  const waitStatus=async(t)=>p.locator('#status').filter({hasText:t}).waitFor();
  await sign('contributor');assert.equal(await p.locator('#validation-section').isVisible(),false);
  await p.locator('#upload-criterion').selectOption('Q01');await p.locator('#upload-request').selectOption('SA-01');
  await fill('upload',{title:'Aurora fictional mandate',sourceOwner:'Synthetic sponsor',period:'FY26',sourceVersion:'1',locator:'Text line 1'});
  await p.locator('#upload [name=file]').setInputFiles({name:'synthetic.txt',mimeType:'text/plain',buffer:Buffer.from('Aurora fictional strategic mandate')});await p.locator('#upload button').click();await waitStatus('Source submitted to quarantine.');await out();
  await sign('assessor');await p.locator('#quarantine').selectOption({index:1});await p.locator('#inspect').click();await p.locator('#quarantine-text').filter({hasText:'Aurora fictional strategic mandate'}).waitFor();await fill('screen',{reason:'Synthetic manual inspection'});await p.locator('#screen button').click();await waitStatus('Disposition recorded.');
  await p.locator('#matching-criterion').selectOption('Q01');await fill('matching-propose',{query:'Aurora fictional strategic mandate'});await p.locator('#matching-propose button').click();await waitStatus('Evidence matching proposals generated; human confirmation required.');
  await p.locator('#matching-results summary').click();await p.locator('#matching-results').getByText('Exact quotation: Aurora fictional strategic mandate').waitFor();await p.locator('#matching-review-id').selectOption({index:1});await p.locator('#matching-review [name=decision]').selectOption('link');await fill('matching-review',{reason:'Fictional relevance review'});await p.locator('#matching-review [name=confirmed]').check();await p.locator('#matching-review button[type=submit], #matching-review button:not([type])').click();await waitStatus('Preview the entire accepted source before confirming a candidate');
  await p.locator('#matching-preview').click();await waitStatus('Accepted source previewed.');await p.locator('#matching-review button[type=submit], #matching-review button:not([type])').click();await waitStatus('Relevance decision recorded; validation still requires separate review.');
  assert.equal(await p.locator('#validation-criterion option').count(),28);await p.locator('#validation-criterion').selectOption('Q01');await fill('validation-draft',{claim:'Aurora synthetic strategy linkage',rationale:'Fictional decision rationale and materiality',owner:'Synthetic sponsor'});
  for(const [k,v] of Object.entries({applicability:'applicable',condition:'met',evidenceClass:'E1',strength:'Strong'}))await p.locator('#validation-draft [name='+k+']').selectOption(v);
  for(const k of ['fieldsVerified','comparable','materialityReviewed'])await p.locator('#validation-draft [name='+k+']').check();
  await p.locator('#validation-match-refs input[type=checkbox]').check();
  await p.locator('#validation-draft button').click();await waitStatus('Validation draft saved; scoring locked.');await p.locator('#validation-drafts').getByText('Q01 · review pending').waitFor();await out();
  await sign('reviewer');await p.locator('#validation-review-id').selectOption({index:1});await p.locator('#validation-review [name=decision]').selectOption('accept');await fill('validation-review',{reason:'Independent fictional source review'});await p.locator('#validation-review [name=confirmed]').check();await p.locator('#validation-review button').click();await waitStatus('Reviewer must preview every linked source');
  await p.locator('#preview-id').selectOption({index:1});await p.locator('#preview').click();await waitStatus('Accepted source previewed.');await p.locator('#validation-review button').click();await waitStatus('Independent validation review recorded.');await out();
  await sign('owner');await p.locator('#validation-drafts').getByText('Q01 · supported met').waitFor();await p.locator('#release').click();await waitStatus('Access denied or release gate locked');
  if(process.env.TCI_SCREENSHOT)await p.locator('#matching-section').screenshot({path:process.env.TCI_SCREENSHOT});
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await out();assert.equal(await p.locator('#validation-drafts article').count(),0);await sign('contributor');assert.equal(await p.locator('#validation-section').isVisible(),false);assert.deepEqual(errors,[]);
  console.log('PASS: synthetic discovery, verified exact quote, relevance refused before source preview, human-confirmed matching citation imported to draft, independent validation, owner supported condition, scoring locked, contributor isolation and mobile width.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
