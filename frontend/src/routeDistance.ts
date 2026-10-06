import type {Reply} from './types';

// Great-circle lengths between verified points; not road or boat routing.
export function illustrativeRoute(coordinates:[number,number][]):Reply['route']{
 if(coordinates.length<2)return null;
 const radians=(degrees:number)=>degrees*Math.PI/180;
 let distance_m=0;
 for(let i=1;i<coordinates.length;i++){
  const [lon1,lat1]=coordinates[i-1], [lon2,lat2]=coordinates[i];
  const h=Math.sin(radians(lat2-lat1)/2)**2+Math.cos(radians(lat1))*Math.cos(radians(lat2))*Math.sin(radians(lon2-lon1)/2)**2;
  distance_m+=6371000*2*Math.asin(Math.min(1,Math.sqrt(h)));
 }
 return {kind:'illustrative',coordinates,distance_m};
}

export function routeDescription(route:NonNullable<Reply['route']>):string{
 const meters=route.distance_m??(route.kind==='illustrative'?illustrativeRoute(route.coordinates)?.distance_m:undefined);
 const value=meters!==undefined&&Number.isFinite(meters)&&meters>=0
  ?`${new Intl.NumberFormat('vi-VN',{maximumFractionDigits:1}).format(meters/1000)} km`:null;
 return route.kind==='actual'
  ?`Quãng đường${value?`: ${value}`:''} · Theo dịch vụ định tuyến`
  :`Tuyến minh họa${value?` · Khoảng cách đường thẳng: ${value}`:''} · Không phải quãng đường đi thực tế`;
}