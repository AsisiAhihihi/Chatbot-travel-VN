import {test,expect} from '@playwright/test';

test('additional missing-place photos load and preserve source credits',async({page})=>{
 await page.goto('/');
 const places=await (await page.request.get('/data/places.json')).json();
 for(const id of ['can_tho_poi_03','da_nang_poi_05','dak_lak_poi_01','dak_lak_poi_03','dien_bien_poi_01','dien_bien_poi_05','gia_lai_poi_03','hue_poi_04']){
  const place=places.find((p:{id:string})=>p.id===id);
  expect(place.image.author).toBeTruthy();expect(place.image.license_url).toBeTruthy();
  expect(place.image.caption).toBeTruthy();
  const image=await page.request.get(place.image.url);
  expect(image.ok()).toBeTruthy();expect(image.headers()['content-type']).toMatch(/image\/(jpeg|png)/);
 }
 await page.locator('nav a[href="/mien-nam"]').click();
 await page.locator('.destinations button').filter({hasText:'Nhà cổ Bình Thủy'}).first().click();
 const popup=page.getByRole('dialog');
 await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
 await expect(popup).toContainText('Nhà cổ Bình Thủy, Cần Thơ');
 await expect(popup.getByRole('link',{name:/Giấy phép:/})).toBeVisible();
});