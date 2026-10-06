import {test,expect} from '@playwright/test';

test('line icons and teardrop sprites retain selection and itinerary numbers',async({page})=>{
 const errors:string[]=[];page.on('pageerror',e=>errors.push(e.message));
 await page.goto('/mien-trung');
 const button=page.locator('.destinations button').filter({hasText:'Hội An'}).first();
 await expect(button.locator('svg.place-icon')).toBeVisible();
 await button.click();
 await expect(page.getByRole('dialog',{name:'Hội An'})).toBeVisible();
 await page.waitForFunction(()=>{
  const m=(document.querySelector('[data-testid="map"]') as any)?.mapInstance;
  return m?.hasImage('pin-history-icon')&&m.queryRenderedFeatures({layers:['points']}).some((f:any)=>f.properties.id==='hoi-an');
 });
 const state=await page.getByTestId('map').evaluate(el=>{
  const m=(el as any).mapInstance;
  return {type:m.getLayer('points').type,anchor:m.getLayoutProperty('points','icon-anchor'),
   selected:m.queryRenderedFeatures({layers:['points']}).find((f:any)=>f.properties.id==='hoi-an')?.properties.selected,
   cluster:m.getLayer('clusters').type};
 });
 expect(state).toEqual({type:'symbol',anchor:'bottom',selected:true,cluster:'circle'});
 await page.screenshot({path:`test-results/${test.info().project.name}-new-pin.png`});
 await page.getByRole('button',{name:'Thêm vào lịch trình',exact:true}).click();
 await expect(button.locator('b')).toHaveText('1');
 await page.waitForFunction(()=>{
  const m=(document.querySelector('[data-testid="map"]') as any)?.mapInstance;
  return m?.hasImage('pin-history-1');
 });
 expect(errors).toEqual([]);
});