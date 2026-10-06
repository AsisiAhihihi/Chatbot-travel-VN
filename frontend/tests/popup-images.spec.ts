import {test,expect} from '@playwright/test';

test('image failure can be retried and reopening resets failure',async({page})=>{
 const place={id:'image-test',name:'Điểm kiểm thử',region:'nam',category:'attraction',coordinates:[105.7,10],description:'Mô tả',aliases:[],source:'https://example.org',image:{url:'/test-image.png',source:'https://example.org'}};
 await page.route('**/data/places.json',r=>r.fulfill({json:[place,{...place,id:'no-image',name:'Điểm chưa có ảnh',image:null}]}));
 let requests=0;
 await page.route('**/test-image.png',async r=>{
  requests++;
  if(requests===1)return r.abort();
  await r.fulfill({contentType:'image/png',body:Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aWQAAAABJRU5ErkJggg==','base64')});
 });
 await page.goto('/');
 await page.locator('.destinations button').filter({hasText:'Điểm kiểm thử'}).click();
 await expect(page.getByRole('status').filter({hasText:'Không tải được ảnh'})).toBeVisible();
 await page.getByRole('button',{name:'Thử tải lại ảnh'}).click();
 await expect.poll(()=>page.locator('.place-popup img').evaluate((img:HTMLImageElement)=>img.naturalWidth)).toBeGreaterThan(0);
 await page.getByRole('button',{name:'Đóng thông tin địa điểm'}).click();
 await page.locator('.destinations button').filter({hasText:'Điểm chưa có ảnh'}).click();
 await expect(page.getByRole('status').filter({hasText:'Chưa có ảnh cho địa điểm này'})).toBeVisible();
 await page.getByRole('button',{name:'Đóng thông tin địa điểm'}).click();
 await page.locator('.destinations button').filter({hasText:'Điểm kiểm thử'}).click();
 await expect(page.locator('.place-popup img')).toBeVisible();
});