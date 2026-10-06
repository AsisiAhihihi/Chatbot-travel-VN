import {useEffect,useRef,useState} from 'react';
import * as maplibregl from 'maplibre-gl';
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url';
import type {GeoJSONSource} from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import {presentationStyle,fitVietnam} from './mapPresentation';
import {categories,regions,type Place,type Region,type Reply} from './types';
import {pinImage} from './PlaceIcon';
export interface View {region:Region|null; focus:Place[];nonce:number}
// Explicitly bundle the v6 worker, including its shared module, for dev and production.
maplibregl.setWorkerUrl(workerUrl);
export function TravelMap({places,view,selected,route,itinerary,onSelect}:{places:Place[];view:View;selected:Place|null;route:Reply['route'];itinerary:string[];onSelect:(p:Place)=>void}) {
 const container=useRef<HTMLDivElement>(null),map=useRef<maplibregl.Map|null>(null);const [ready,setReady]=useState(false),[error,setError]=useState(false);const select=useRef(onSelect);select.current=onSelect;
 const current=useRef(places);current.current=places;
 const currentView=useRef(view);currentView.current=view;
 useEffect(()=>{
  if(!container.current)return;
  const abort=new AbortController();
  let m:maplibregl.Map;try {m=new maplibregl.Map({container:container.current,style:{version:8,sources:{},layers:[{id:'loading-sea',type:'background',paint:{'background-color':'#bcded5'}}]},center:[107,16],zoom:4.5,attributionControl:false});}catch{setError(true);return;}
  map.current=m;m.addControl(new maplibregl.AttributionControl({compact:true}),'bottom-left');
  m.getCanvas().setAttribute('aria-label','Bản đồ Việt Nam, dùng phím mũi tên để di chuyển');
  m.on('error',()=>setError(true));
  const setup=()=>{
   if(!m.getLayer('vn-geographic-labels')||m.getSource('places'))return;
   setError(false);
   m.addSource('places',{type:'geojson',data:{type:'FeatureCollection',features:[]},cluster:true,clusterRadius:42,clusterMaxZoom:11});
   m.addLayer({id:'clusters',type:'circle',source:'places',filter:['has','point_count'],paint:{'circle-color':'#174b3a','circle-radius':22,'circle-stroke-width':3,'circle-stroke-color':'#f7f5ec'}});
   m.addLayer({id:'cluster-count',type:'symbol',source:'places',filter:['has','point_count'],layout:{'text-field':['get','point_count_abbreviated'],'text-size':13},paint:{'text-color':'#ffffff'}});
    m.addLayer({id:'points',type:'symbol',source:'places',filter:['!', ['has','point_count']],layout:{'icon-image':['get','pin'],'icon-anchor':'bottom','icon-size':['case',['get','selected'],1.18,0.9],'icon-allow-overlap':true,'icon-ignore-placement':true,'symbol-sort-key':['case',['get','selected'],1,0]}});
   m.addSource('route',{type:'geojson',data:{type:'FeatureCollection',features:[]}});
   m.addLayer({id:'route-line',type:'line',source:'route',paint:{'line-color':'#b75e3e','line-width':3,'line-dasharray':[2,2]}});
   m.on('click','points',e=>{const p=current.current.find(p=>p.id===e.features?.[0].properties.id);if(p)select.current(p);});
   m.on('click','clusters',async e=>{const f=e.features?.[0];if(!f||f.geometry.type!=='Point')return;const zoom=await (m.getSource('places') as GeoJSONSource).getClusterExpansionZoom(f.properties.cluster_id);m.easeTo({center:f.geometry.coordinates as [number,number],zoom,duration:matchMedia('(prefers-reduced-motion: reduce)').matches?0:450});});
   for(const id of ['points','clusters']){m.on('mouseenter',id,()=>m.getCanvas().style.cursor='pointer');m.on('mouseleave',id,()=>m.getCanvas().style.cursor='');}
   setReady(true);
  };
  m.on('style.load',setup);
  presentationStyle(abort.signal).then(style=>{if(!abort.signal.aborted)m.setStyle(style);}).catch(()=>{if(!abort.signal.aborted)setError(true);});
  const resize=new ResizeObserver(()=>{m.resize();if(m.getSource('places')&&!currentView.current.region&&!currentView.current.focus.length)fitVietnam(m);});resize.observe(container.current);
  // Development-only inspection hook for real WebGL rendering regression tests.
  if(import.meta.env.DEV)(container.current as HTMLDivElement & {mapInstance?:maplibregl.Map}).mapInstance=m;
  return()=>{abort.abort();resize.disconnect();m.remove();};
 },[]);
  useEffect(()=>{if(!ready)return;const m=map.current!;const features=places.filter(p=>p.coordinates&&p.map_usage!=='zoom_only').map(p=>{
   const number=itinerary.includes(p.id)?itinerary.indexOf(p.id)+1:undefined;
   const pin=`pin-${p.category}-${number??'icon'}`;
   if(!m.hasImage(pin))m.addImage(pin,pinImage(p.category,number),{pixelRatio:2});
   return {type:'Feature' as const,geometry:{type:'Point' as const,coordinates:p.coordinates!},properties:{id:p.id,name:p.resolved_name||p.name,pin,selected:selected?.id===p.id}};
  });(m.getSource('places') as GeoJSONSource).setData({type:'FeatureCollection',features});},[ready,places,selected,itinerary]);
 useEffect(()=>{if(!ready)return;const m=map.current!,coords=view.focus.flatMap(p=>p.coordinates?[p.coordinates]:[]);const duration=matchMedia('(prefers-reduced-motion: reduce)').matches?0:850;
 if(coords.length===1)m.flyTo({center:coords[0],zoom:view.focus[0]?.map_usage==='zoom_only'?10:12,duration});
 else if(coords.length>1){const bounds=new maplibregl.LngLatBounds();coords.forEach(c=>bounds.extend(c));m.fitBounds(bounds,{padding:{top:100,bottom:110,left:65,right:65},maxZoom:10,duration});}
 else if(view.region)m.flyTo({...regions[view.region],duration});
  else fitVietnam(m,duration);
 },[view,ready]);
 useEffect(()=>{if(!ready)return;const m=map.current!;(m.getSource('route') as GeoJSONSource).setData({type:'FeatureCollection',features:route? [{type:'Feature',properties:{},geometry:{type:'LineString',coordinates:route.coordinates}}]:[]});m.setPaintProperty('route-line','line-dasharray',route?.kind==='actual'?[1,0]:[2,2]);},[ready,route]);
 return <><div ref={container} className="map-canvas" data-testid="map"/><div className="zoom-controls"><button aria-label="Phóng to" onClick={()=>map.current?.zoomIn()}>＋</button><button aria-label="Thu nhỏ" onClick={()=>map.current?.zoomOut()}>−</button></div>{error&&<div className="map-error" role="status">Bản đồ nền chưa tải được. Bạn vẫn có thể chọn địa điểm và trò chuyện.</div>}</>;
}