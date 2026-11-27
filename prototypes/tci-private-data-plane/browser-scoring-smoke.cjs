const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process'),readline=require('node:readline'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0','--enable-pilot-scoring'],{stdio:['ignore','pipe','pipe'],env:process.env});
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
  assert.equal(await p.locator('#validation-criterion option').count(),28);await p.locator('#validation-criterion').selectOption('Q01');await fill('validation-draft',{claim:'Aurora synthetic strategy linkage',rationale:'Fictional decision rationale and materiality',owner:'Synthetic sponsor'});
  for(const [k,v] of Object.entries({applicability:'applicable',condition:'met',evidenceClass:'E1',strength:'Strong'}))await p.locator('#validation-draft [name='+k+']').selectOption(v);
  for(const k of ['fieldsVerified','comparable','materialityReviewed'])await p.locator('#validation-draft [name='+k+']').check();
  await p.locator('#validation-refs input[type=checkbox]').check();await p.locator('#validation-refs [data-field=locator]').fill('Text line 1');await p.locator('#validation-refs [data-field=quote]').fill('Aurora fictional strategic mandate');
  await p.locator('#validation-draft button').click();await waitStatus('Validation draft saved; scoring locked.');await p.locator('#validation-drafts').getByText('Q01 · review pending').waitFor();await out();
  await sign('reviewer');await p.locator('#validation-review-id').selectOption({index:1});await p.locator('#validation-review [name=decision]').selectOption('accept');await fill('validation-review',{reason:'Independent fictional source review'});await p.locator('#validation-review [name=confirmed]').check();await p.locator('#validation-review button').click();await waitStatus('Reviewer must preview every linked source');
  await p.locator('#preview-id').selectOption({index:1});await p.locator('#preview').click();await waitStatus('Accepted source previewed.');await p.locator('#validation-review button').click();await waitStatus('Independent validation review recorded.');await out();
  await sign('assessor');await p.locator('#pilot-score-criterion').selectOption('Q01');await p.locator('#pilot-score-draft [name=score]').selectOption('3');await fill('pilot-score-draft',{rationale:'Minimum condition verified on fictional evidence',redFlag:'Synthetic risk for review'});await p.locator('#pilot-score-draft button').click();await waitStatus('Synthetic score proposal recorded.');await out();
  await sign('reviewer');await p.locator('#pilot-score-review-id').selectOption({index:1});await p.locator('#pilot-score-review [name=decision]').selectOption('accept');await fill('pilot-score-review',{reason:'Independently reviewed synthetic anchor'});await p.locator('#pilot-score-review [name=confirmed]').check();await p.locator('#pilot-score-review button').click();await waitStatus('Independent pilot score review recorded.');await out();
  await sign('owner');await p.locator('#validation-drafts').getByText('Q01 · supported met').waitFor();await p.locator('#pilot-score-records').getByText('Q01 · proposed 3 · accepted').waitFor();await p.locator('#pilot-score-summary').getByText('1/28').waitFor();assert.equal(await p.locator('#pilot-score-summary').getByText('Withheld',{exact:true}).count(),2);await p.locator('#release').click();await waitStatus('Access denied or release gate locked');
  if(process.env.TCI_SCREENSHOT)await p.locator('#pilot-scoring-section').screenshot({path:process.env.TCI_SCREENSHOT});
  await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);await out();assert.equal(await p.locator('#validation-drafts article').count(),0);await sign('contributor');assert.equal(await p.locator('#validation-section').isVisible(),false);assert.equal(await p.locator('#pilot-scoring-section').isVisible(),false);assert.deepEqual(errors,[]);
  console.log('PASS: Aurora synthetic evidence validation, explicit score anchor proposal, independent score review, owner 1/28 coverage, canonical withheld, production locked, contributor isolation and mobile width.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
