import {readFileSync,writeFileSync,unlinkSync,existsSync} from 'node:fs';
import {publicImageAllowed} from '../imagePolicy.mjs';
const catalogue=new URL('../dist/data/places.json',import.meta.url);
const places=JSON.parse(readFileSync(catalogue,'utf8'));
const permitted=new Set(places.filter(p=>publicImageAllowed(p.image)).map(p=>p.image?.url));
let hidden=0;
for(const place of places){
 if(publicImageAllowed(place.image))continue;
 if(!place.image)continue;
 const url=place.image.url;
 if(url.startsWith('/images/')&&!permitted.has(url)){
  const file=new URL(`../dist/${url.slice(1)}`,import.meta.url);
  if(existsSync(file))unlinkSync(file);
 }
 delete place.image;hidden++;
}
writeFileSync(catalogue,JSON.stringify(places)+'\n');
console.log(`Public catalogue: ${places.length} destinations; ${hidden} permission-required images hidden.`);