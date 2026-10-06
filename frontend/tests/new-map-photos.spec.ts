import {test,expect} from '@playwright/test';

test('new destination photos load locally and retain credits',async({page})=>{
 await page.goto('/');
 const response=await page.request.get('/data/places.json');
 const places=await response.json();
 for(const id of ['an_giang_poi_02_b','ninh_binh_poi_01_b','hue_poi_03_b','lam_dong_poi_05_b']){
  const place=places.find((p:{id:string})=>p.id===id);
  expect(place.image.author).toBeTruthy();
  expect(place.image.license).toBeTruthy();
  expect(place.image.source).toContain('commons.wikimedia.org');
  const image=await page.request.get(place.image.url);
  expect(image.ok()).toBeTruthy();
  expect(image.headers()['content-type']).toMatch(/image\/(jpeg|png)/);
 }
 await page.locator('nav a[href="/mien-bac"]').click();
 const button=page.locator('.destinations button').filter({hasText:'Tam Cốc'}).first();
 await button.click();
 const popup=page.getByRole('dialog',{name:'Tam Cốc'});
 await expect(popup).toBeVisible();
 await expect(popup.locator('img')).toBeVisible();
 await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
 const tamCoc=places.find((p:{id:string})=>p.id==='ninh_binh_poi_01_b');
 await expect(popup).toContainText(tamCoc.image.license);
 await expect(popup).toContainText(tamCoc.image.author);
});