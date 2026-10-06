import {test,expect} from '@playwright/test';
test('Pages base, refresh, permitted images and API paths',async({page,request})=>{
 const base='/Chatbot-travel-VN/';
 const response=await request.get(`${base}data/places.json`);
 expect(response.ok()).toBeTruthy();
 const places=await response.json();
 expect(places).toHaveLength(209);
 expect(places.filter((p:any)=>p.image)).toHaveLength(185);
 for(const p of places.filter((p:any)=>p.image))expect(p.image.rights_status).not.toBe('permission_required');
 const photo=places.find((p:any)=>p.image?.url.startsWith('/images/'));
 expect((await request.get(base+photo.image.url.slice(1))).ok()).toBeTruthy();
 expect((await request.get(`${base}geo/vietnam.geojson`)).ok()).toBeTruthy();
 await page.goto(`${base}#/mien-nam`);
 await expect(page.getByTestId('map')).toBeVisible();
 await expect(page.locator('.destinations')).toContainText('Cần Giờ');
 await expect(page.locator('.destinations')).not.toContainText('Hồ Gươm');
 await page.reload();
 await expect(page.locator('.destinations')).toContainText('Cần Giờ');
});