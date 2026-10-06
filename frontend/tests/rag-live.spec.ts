import {test,expect} from '@playwright/test';

test('live RAG response opens verified destination popup',async({page},info)=>{
 test.skip(process.env.RAG_LIVE!=='1','Opt-in: requires running FastAPI, index and Ollama');
 test.setTimeout(240000);
 await page.goto('/');
 if(info.project.name==='mobile')await page.getByRole('button',{name:'Trò chuyện cùng Mây',exact:true}).click();
 const response=page.waitForResponse(r=>r.url().endsWith('/chat')&&r.request().method()==='POST',{timeout:200000});
 await page.getByRole('button',{name:'Hội An có gì?',exact:true}).click();
 const result=await response;
 expect(result.ok()).toBeTruthy();
 const data=await result.json();
 expect(data.sources.length).toBeGreaterThan(0);
 expect(data.places[0].id).toBe('hoi-an');
 await expect(page.getByRole('dialog',{name:'Hội An'})).toBeVisible();
 await expect(page).toHaveURL(/mien-trung$/);
 await page.screenshot({path:`test-results/${info.project.name}-rag-live.png`});
});