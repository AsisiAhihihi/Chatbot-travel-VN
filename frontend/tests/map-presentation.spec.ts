import {test,expect} from '@playwright/test';

test('geographic layers render and retain map interactions',async({page},info)=>{
 test.setTimeout(120000);
 const errors:string[]=[];
 page.on('pageerror',error=>errors.push(error.message));
 await page.goto('/');
 await page.waitForFunction(()=>{
  const m=(document.querySelector('[data-testid="map"]') as any)?.mapInstance;
  return m?.getSource('places') && m.isSourceLoaded('vn-labels');
 },{},{timeout:90000});
 await page.waitForTimeout(1500);
 const state=await page.evaluate(()=>{
  const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
  const layers=m.getStyle().layers;
  return {labels:[...new Set(m.queryRenderedFeatures({layers:['vn-geographic-labels']}).map((f:any)=>f.properties.label))],
   masks:layers.filter((l:any)=>['vn-ocean','vn-surrounding-land'].includes(l.id)).length,
   sources:Object.keys(m.getStyle().sources),
   sea:m.getPaintProperty('water','fill-color'),
   symbols:m.queryRenderedFeatures({layers:['vn-island-symbols']}).length,
   filtered:layers.filter((l:any)=>l.type==='symbol'&&l.layout?.['text-field']!==undefined&&l.layout?.visibility!=='none'&&!['places','vn-labels'].includes(l.source)).every((l:any)=>JSON.stringify(l.filter).includes('within')),
   transportAboveWater:layers.filter((l:any)=>l['source-layer']==='transportation').every((l:any)=>layers.indexOf(l)>layers.findIndex((l:any)=>l.id==='water'))};
  });
  expect(state.masks).toBe(0);expect(state.sources).not.toContain('vn-ocean');expect(state.sources).not.toContain('vn-surrounding-land');
  expect(state.sea).toBe('#bcded5');expect(state.filtered).toBeTruthy();expect(state.transportAboveWater).toBeTruthy();
  expect(state.labels).toEqual(expect.arrayContaining(['Biển Đông','Quần đảo Hoàng Sa (Việt Nam)','Quần đảo Trường Sa (Việt Nam)']));
   expect(state.symbols).toBeGreaterThan(0);
   const boundaries=await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    return ['boundary_2','boundary_disputed','boundary_3'].map(id=>({id,visibility:m.getLayoutProperty(id,'visibility'),color:m.getPaintProperty(id,'line-color'),dash:m.getPaintProperty(id,'line-dasharray'),filter:m.getFilter(id)}));
   });
   for(const layer of boundaries.slice(0,2)){
    expect(layer.visibility).toBe('visible');
    expect(layer.color).toBe('#668477');
    expect(layer.filter).toContainEqual(['==',['get','admin_level'],2]);
    expect(layer.filter).toContainEqual(['!=',['get','maritime'],1]);
   }
   expect(boundaries[1].dash).toEqual([1,2]);
   expect(boundaries[2].visibility).toBe('none');
   const language=await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    const layers=m.getStyle().layers;
    return {
     names:layers.filter((l:any)=>l.type==='symbol'&&l.layout?.visibility!=='none'&&/"name(?::[^"]*|_[^"]*)?"/.test(JSON.stringify(l.layout?.['text-field'])||'')).map((l:any)=>l.layout['text-field']),
     shield:m.getLayoutProperty('highway-shield-non-us','text-field'),
    };
   });
   expect(language.names.length).toBeGreaterThan(5);
   for(const expression of language.names)expect(expression).toEqual(['case',
    ['!=',['coalesce',['get','name:vi'],''],''],['get','name:vi'],
    ['!=',['coalesce',['get','name_vi'],''],''],['get','name_vi'],
    ['coalesce',['get','name'],'']]);
   expect(language.shield).toEqual(['to-string',['get','ref']]);
   await page.screenshot({path:`test-results/${info.project.name}-vietnam.png`});
  for(const [name,center,zoom] of [
   ['dai-ngai-regional',[106.15,9.75],10],['dai-ngai',[106.15,9.75],12],['dai-ngai-detail',[106.15,9.75],14],
   ['nha-trang',[109.19,12.25],12],['da-nang',[108.23,16.07],12],
   ['cambodia',[104.92,11.56],12],['thailand',[100.5,13.75],10],['china',[108.32,22.82],10],['laos',[102.63,17.97],10],
  ] as const){
   await page.evaluate(({center,zoom})=>(document.querySelector('[data-testid="map"]') as any).mapInstance.jumpTo({center:[...center],zoom}),{center,zoom});
   await page.waitForFunction(()=>(document.querySelector('[data-testid="map"]') as any).mapInstance.areTilesLoaded(),{},{timeout:45000});
   await page.waitForTimeout(500);
   const features=await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    const fs=m.queryRenderedFeatures();
    return {roads:fs.filter((f:any)=>f.layer['source-layer']==='transportation').length,
     bridges:fs.filter((f:any)=>f.layer.id.startsWith('bridge_')).length,
     names:fs.filter((f:any)=>f.layer.type==='symbol'&&f.layer.layout?.['text-field']!==undefined&&f.source!=='places'&&f.source!=='vn-labels').map((f:any)=>f.properties.name)};
   });
   expect(features.roads,name).toBeGreaterThan(0);
   if(['cambodia','thailand','china','laos'].includes(name))expect(features.names,name).toEqual([]);
   if(name==='da-nang')expect(features.bridges).toBeGreaterThan(0);
   await page.screenshot({path:`test-results/${info.project.name}-${name}.png`});
  if(name==='nha-trang'){
   const labels=await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    return m.queryRenderedFeatures({layers:['label_town','label_city','label_village','label_other']}).map((f:any)=>f.properties.name);
   });
   expect(labels).toContain('Nha Trang');
   await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    m.panBy([85,35],{duration:0});
   });
   await page.waitForFunction(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    return !m.isMoving()&&m.areTilesLoaded();
   });
   const afterPan=await page.evaluate(()=>{
    const m=(document.querySelector('[data-testid="map"]') as any).mapInstance;
    return m.queryRenderedFeatures({layers:['label_town','label_city','label_village','label_other']}).map((f:any)=>f.properties.name);
   });
   expect(afterPan).toContain('Nha Trang');
   await page.screenshot({path:`test-results/${info.project.name}-nha-trang-panned-coastal-labels.png`});
  }
 }
 await page.getByRole('button',{name:'Toàn Việt Nam'}).click();
 await expect.poll(()=>page.evaluate(()=>(document.querySelector('[data-testid="map"]') as any).mapInstance.getZoom())).toBeLessThan(7);
 await page.getByRole('button',{name:'Phóng to',exact:true}).click();
 await page.getByRole('button',{name:'Thu nhỏ',exact:true}).click();
 expect(errors).toEqual([]);
});
