// Render our own local artifacts; no user browser session or remote site access.
const {chromium}=require('C:/Users/Administrator/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs=require('fs');
const {pathToFileURL}=require('url');
(async()=>{
  const root='D:/STGPlanner/codex/outputs';
  const summary=JSON.parse(fs.readFileSync(root+'/gbp2_optimization_20261028/summary.json','utf8'));
  const browser=await chromium.launch({headless:true,channel:'msedge'});
  const page=await browser.newPage({viewport:{width:1680,height:1100}});
  const results=[];
  for(const name of ['GBP2优化测试报告','Scene4四算法与论文对比汇总','代码目录说明']){
    await page.goto(pathToFileURL(root+'/'+name+'.html').href,{waitUntil:'load'});
    const result=await page.evaluate(()=>({
      pageWidth:document.documentElement.clientWidth,scrollWidth:document.documentElement.scrollWidth,
      brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,
      tableCount:document.querySelectorAll('table').length,text:document.body.innerText
    }));
    if(result.pageWidth!==result.scrollWidth||result.brokenImages)throw new Error(name+JSON.stringify(result));
    if(name==='GBP2优化测试报告'){
      for(const record of summary.records)if(!result.text.includes(record.trial))throw new Error('Missing trial:'+record.trial);
      if(!result.text.includes('0.5192')||!result.text.includes('130m'))throw new Error('Missing geometry/range scope');
      await page.screenshot({path:root+'/gbp2_optimization_20261028/report_preview.png',fullPage:false});
    }
    delete result.text;results.push({report:name,...result});
  }
  await browser.close();
  fs.writeFileSync(root+'/gbp2_optimization_20261028/report_layout.json',JSON.stringify({all_passed:true,results},null,2)+'\n');
  console.log(JSON.stringify(results));
})().catch(error=>{console.error(error.message);process.exit(1);});
