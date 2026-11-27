const {chromium}=require(process.env.PLAYWRIGHT_MODULE||'playwright');
const {spawn}=require('node:child_process'),readline=require('node:readline'),path=require('node:path'),assert=require('node:assert/strict');
(async()=>{
 if(!process.env.TCI_AURORA_WORKBOOK)throw Error('Set TCI_AURORA_WORKBOOK to fingerprinted fictional source');
 const proc=spawn(process.env.TCI_PYTHON||'python3',[path.join(__dirname,'serve.py'),'--port','0','--enable-pilot-scoring','--aurora-pilot-workbook',process.env.TCI_AURORA_WORKBOOK],{stdio:['ignore','pipe','pipe'],env:process.env});
 const rl=readline.createInterface({input:proc.stdout});let browser;
 try{
  const cfg=await new Promise((resolve,reject)=>{rl.once('line',x=>{try{resolve(JSON.parse(x));}catch(e){reject(e);}});proc.once('exit',()=>reject(Error('Synthetic pilot server stopped')));});
  browser=await chromium.launch({channel:'chrome',headless:true});const p=await browser.newPage({viewport:{width:1280,height:900}});p.setDefaultTimeout(15000);const errors=[];p.on('pageerror',e=>errors.push(e.message));await p.goto(cfg.url);
  const sign=async(role)=>{await p.locator('#login [name=username]').fill(role);await p.locator('#login [name=password]').fill(cfg.users[role]);await p.locator('#login button').click();await p.getByText('Signed in as '+role).waitFor();};
  const out=async()=>{await p.locator('#logout').click();await p.locator('#login-section').waitFor({state:'visible'});};
  await sign('owner');await p.locator('#aurora-pilot-section').getByText('27/28',{exact:true}).waitFor();assert.equal(await p.locator('#interview-claims article').count(),30);assert.equal(await p.locator('#validation-drafts article').count(),28);
  await p.locator('#interview-conflicts').getByText(/Programme reported versus Finance-validated benefit/).waitFor();await p.locator('#pilot-score-summary').getByText('0/28',{exact:true}).waitFor();await p.locator('#executive-briefs').getByText(/Owner direction: Reassess/).waitFor();
  await p.locator('#reassessment-summary').getByText('Accepted snapshots').waitFor();assert.equal(await p.locator('#reassessment-snapshots article').count(),0);
  if(process.env.TCI_SCREENSHOT)await p.locator('#aurora-pilot-section').screenshot({path:process.env.TCI_SCREENSHOT});
  if(process.env.TCI_EXECUTIVE_SCREENSHOT)await p.locator('#executive-section').screenshot({path:process.env.TCI_EXECUTIVE_SCREENSHOT});
  await p.locator('#release').click();await p.locator('#status').filter({hasText:'Access denied or release gate locked'}).waitFor();await p.setViewportSize({width:390,height:844});assert.equal(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
  await out();await sign('contributor');for(const id of ['aurora-pilot-section','interviews-section','validation-section','pilot-scoring-section','executive-section','reassessment-section'])assert.equal(await p.locator('#'+id).isVisible(),false);assert.deepEqual(errors,[]);
  console.log('PASS: fingerprinted Aurora workbook, 29 responses/30 claims, 28 unresolved drafts, material benefit conflict, zero accepted scores, reviewed synthetic Reassess, no invented historical snapshot, locked release, contributor isolation, mobile width.');
 }finally{if(browser)await browser.close();rl.close();proc.kill();}
})().catch(e=>{console.error(e);process.exit(1)});
