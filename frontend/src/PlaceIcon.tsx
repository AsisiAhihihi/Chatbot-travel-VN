import {categories,type Category} from './types';

// One set of original line drawings shared by React and map sprites.
const paths:Record<Category,string[]>={
 attraction:['M12 21s7-7 7-12a7 7 0 0 0-14 0c0 5 7 12 7 12Z','M9 9a3 3 0 1 0 6 0a3 3 0 1 0-6 0'],
 nature:['M2 20 9 5l5 10 3-6 5 11H2Z','m6 11 3 3 3-3'],
 beach:['M2 11c3-4 5 4 8 0s5 4 8 0 3 0 4 0','M2 17c3-4 5 4 8 0s5 4 8 0 3 0 4 0','M15 3v3m-3-1 2 2m4-2-2 2'],
 history:['M3 9h18L12 3 3 9Z','M5 10v9m5-9v9m4-9v9m5-9v9M3 21h18'],
 food:['M3 12h18c0 5-4 8-9 8s-9-3-9-8Z','M9 3l3 7m3-8 2 8M7 22h10'],
 stay:['M3 20V7m18 13V7M3 16h18M3 11h18v5M6 8h4v3H6Zm8 0h4v3h-4Z'],
};

export function PlaceIcon({category}:{category:Category}){
 return <svg className="place-icon" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[category].map((d,i)=><path key={i} d={d}/>)}</svg>;
}

export function pinImage(category:Category,number?:number):ImageData{
 const canvas=document.createElement('canvas');canvas.width=80;canvas.height=100;
 const ctx=canvas.getContext('2d');if(!ctx)throw new Error('Không thể tạo icon bản đồ.');
 ctx.scale(2,2);
 ctx.fillStyle=categories[category].color;ctx.strokeStyle='#f7f5ec';ctx.lineWidth=2;
 ctx.fill(new Path2D('M20 48C17 42 3 31 3 20a17 17 0 0 1 34 0c0 11-14 22-17 28Z'));
 ctx.stroke(new Path2D('M20 48C17 42 3 31 3 20a17 17 0 0 1 34 0c0 11-14 22-17 28Z'));
 if(number!==undefined){
  ctx.fillStyle='#fff';ctx.font='600 14px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';ctx.fillText(String(number),20,20,26);
 }else{
  ctx.save();ctx.translate(10,9);ctx.scale(20/24,20/24);ctx.strokeStyle='#fff';ctx.lineWidth=1.8;ctx.lineCap='round';ctx.lineJoin='round';
  paths[category].forEach(d=>ctx.stroke(new Path2D(d)));ctx.restore();
 }
 return ctx.getImageData(0,0,80,100);
}