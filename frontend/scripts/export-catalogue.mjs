import {readFileSync,writeFileSync,mkdirSync} from 'node:fs';
const records=JSON.parse(readFileSync(new URL('../../src/rag/catalogue.json',import.meta.url),'utf8'));
const keys=['id','name','region','category','coordinates','description','duration','image','source','aliases','coordinate_source','coordinate_note','resolved_name','map_usage','coordinate_type','navigation_ready'];
const places=records.map(record=>Object.fromEntries(keys.filter(key=>record[key]!==undefined).map(key=>[key,record[key]])));
const directory=new URL('../public/data/',import.meta.url);
mkdirSync(directory,{recursive:true});
writeFileSync(new URL('places.json',directory),JSON.stringify(places)+'\n','utf8');
console.log(`Exported ${places.length} frontend destinations without backend metadata.`);