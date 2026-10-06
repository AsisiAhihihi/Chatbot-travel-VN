import fs from 'node:fs';
import crypto from 'node:crypto';
import {chromium} from '@playwright/test';

// Only replace existing file redirects when the direct file actually returns an image.
const path=new URL('../../src/rag/catalogue_overrides.json',import.meta.url);
const places=JSON.parse(fs.readFileSync(path,'utf8'));
const browser=await chromium.launch();
const context=await browser.newContext();
const results=[];
try {
 for(const place of places.filter(p=>p.image?.url)) {
  const original=place.image.url;
  const url=new URL(original);
  let candidate=original;
  if(url.hostname==='commons.wikimedia.org') {
   const raw=url.searchParams.get('title')||decodeURIComponent(url.pathname);
   const filename=raw.split(/Special:(?:FilePath|Redirect\/file)\//i)[1]?.replaceAll(' ','_');
   if(filename) {
    const hash=crypto.createHash('md5').update(filename).digest('hex');
    candidate=`https://upload.wikimedia.org/wikipedia/commons/${hash[0]}/${hash.slice(0,2)}/${encodeURIComponent(filename)}`;
   }
  }
  try {
   const response=await context.request.get(candidate,{timeout:15000});
   const contentType=response.headers()['content-type']||'';
   const ok=response.ok()&&contentType.startsWith('image/');
   if(ok)place.image.url=response.url();
   results.push({id:place.id,original,candidate,status:response.status(),contentType,updated:ok&&original!==place.image.url});
   await response.dispose();
  } catch(error) {results.push({id:place.id,original,candidate,error:String(error)});}
 }
 fs.writeFileSync(path,JSON.stringify(places,null,2)+'\n');
 fs.writeFileSync(new URL('../image-url-audit.json',import.meta.url),JSON.stringify(results,null,2)+'\n');
 console.log(JSON.stringify(results,null,2));
} finally {await browser.close();}