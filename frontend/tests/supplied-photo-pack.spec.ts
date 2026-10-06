import {test,expect} from '@playwright/test';
import {readFileSync} from 'node:fs';

test('packaged licensed photos are served by ID with caption and attribution',async({page})=>{
 const pack=JSON.parse(readFileSync('../nguon_anh_95_dia_diem/poi_image_sources.json','utf8'));
 await page.goto('/');
 const response=await page.request.get('/data/places.json');
 const places=await response.json();
 for(const row of pack.filter((r:{status:string})=>r.status==='licensed_photo_available')){
  const place=places.find((p:{id:string})=>p.id===row.id);
  const photo=row.images.find((p:{local_path?:string})=>p.local_path);
  expect(place.image.caption).toBe(photo.caption);
  expect(place.image.author).toBe(photo.author);
  expect(place.image.source).toBe(photo.source_page_url);
  const image=await page.request.get(place.image.url);
  expect(image.ok()).toBeTruthy();
  expect(image.headers()['content-type']).toMatch(/image\/(jpeg|png)/);
 }
 await page.locator('nav a[href="/mien-nam"]').click();
 await page.locator('.destinations button').filter({hasText:'Cồn Sơn'}).first().click();
 const popup=page.getByRole('dialog');
 const place=places.find((p:{id:string})=>p.id==='can_tho_poi_04');
 await expect(popup.locator('img')).toHaveAttribute('alt',place.image.caption);
 await expect.poll(()=>popup.locator('img').evaluate((img:HTMLImageElement)=>img.complete&&img.naturalWidth>0)).toBe(true);
 await expect(popup).toContainText(place.image.caption);
 await expect(popup).toContainText(place.image.author);
 await expect(popup.getByRole('link',{name:`Giấy phép: ${place.image.license}`,exact:true})).toHaveAttribute('href',place.image.license_url);
});