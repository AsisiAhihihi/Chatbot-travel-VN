import type {Map, StyleSpecification, FilterSpecification} from 'maplibre-gl';
import type {FeatureCollection} from 'geojson';

const geo = (name:string) => `${import.meta.env.BASE_URL}geo/${name}.geojson`;
export async function presentationStyle(signal:AbortSignal):Promise<StyleSpecification> {
 const [response, country] = await Promise.all([
  fetch(import.meta.env.VITE_MAP_STYLE_URL || 'https://tiles.openfreemap.org/styles/liberty',{signal}),
  fetch(geo('vietnam'),{signal}),
 ]);
 if(!response.ok || !country.ok)throw new Error('Không tải được dữ liệu bản đồ');
 const style:StyleSpecification=await response.json(), vietnam:FeatureCollection=await country.json();
 // A raster with baked-in labels cannot satisfy the geographic label filters.
 for(const layer of style.layers){
  if(layer.type==='background')layer.paint={...layer.paint,'background-color':'#dce7cd'};
  if(layer.type==='fill'&&/water/.test(layer.id))layer.paint={...layer.paint,'fill-color':'#bcded5'};
  if(layer.type==='fill'&&/wood|forest|park/.test(layer.id))layer.paint={...layer.paint,'fill-color':'#9eba9a'};
  if(/wetland/.test(layer.id))layer.layout={...layer.layout,visibility:'none'};
   if(layer.type==='symbol' && layer.layout?.['text-field']!==undefined){
    if(layer['source-layer']==='water_name')layer.layout={...layer.layout,visibility:'none'};
   else {
    layer.filter=['all',...(layer.filter?[layer.filter]:[]),['within',vietnam]] as FilterSpecification;
    // Localize name labels only: route references/shields must keep their expressions.
    if(/"name(?::[^"]*|_[^"]*)?"/.test(JSON.stringify(layer.layout['text-field']))){
     layer.layout={...layer.layout,'text-field':['case',
      ['!=',['coalesce',['get','name:vi'],''],''],['get','name:vi'],
      ['!=',['coalesce',['get','name_vi'],''],''],['get','name_vi'],
      ['coalesce',['get','name'],'']]};
    }
   }
  }
  if(layer.type==='line' && ['boundary_2','boundary_disputed'].includes(layer.id)){
   // Reuse provider geometry and dispute flags; never add maritime claims.
   layer.filter=['all',...(layer.filter?[layer.filter]:[]),['==',['get','admin_level'],2],['!=',['get','maritime'],1]] as FilterSpecification;
   layer.layout={...layer.layout,visibility:'visible'};
   layer.paint={...layer.paint,'line-color':'#668477','line-opacity':0.8,'line-width':['interpolate',['linear'],['zoom'],3,0.7,6,1,12,1.5]};
  }
  else if(layer.type==='fill-extrusion'||/boundary/.test(layer.id)||(layer.type==='raster'&&layer.id!=='natural_earth'))layer.layout={...layer.layout,visibility:'none'};
 }
  // Use the basemap's matched water/land geometry and original transport order.
  // Generalized Natural Earth ocean/country fills obscure detailed coastlines
  // and bridges at street zoom; never use them as opaque basemap masks.
  for(const name of ['islands','island-symbols','labels'])style.sources[`vn-${name}`]={type:'geojson',data:geo(name),tolerance:0,maxzoom:18,attribution:`<a href="https://www.naturalearthdata.com/">Natural Earth</a> · <a href="${import.meta.env.BASE_URL}geo/README.md">Nguồn địa lý & lưu ý chủ quyền</a>`};
   // Small archipelago land polygons belong below transport, not above bridges.
   const firstTransportLayer=style.layers.findIndex(layer=>'source-layer' in layer && layer['source-layer']==='transportation');
   if(firstTransportLayer<0)throw new Error('Bản đồ nền thiếu lớp giao thông vector');
   style.layers.splice(firstTransportLayer,0,{id:'vn-island-land',type:'fill',source:'vn-islands',paint:{'fill-color':'#9eba9a'}});
  const firstTextLayer=style.layers.findIndex(layer=>layer.type==='symbol' && layer.layout?.['text-field']!==undefined);
  if(firstTextLayer<0)throw new Error('Bản đồ nền thiếu lớp nhãn chữ vector');
  style.layers.splice(firstTextLayer,0,
  {id:'vn-island-symbols',type:'circle',source:'vn-island-symbols',paint:{'circle-radius':['interpolate',['linear'],['zoom'],2,1.5,6,2.5,12,2],'circle-color':'#527e68','circle-opacity':0.8,'circle-stroke-color':'#e4f1e8','circle-stroke-width':0.6}},
  {id:'vn-geographic-labels',type:'symbol',source:'vn-labels',layout:{'text-field':['get','label'],'text-font':['Noto Sans Regular'],'text-size':['case',['==',['get','kind'],'sea'],16,12],'text-max-width':11,'text-anchor':'top','text-offset':[0,0.7],'text-allow-overlap':true,'text-ignore-placement':true},paint:{'text-color':'#386956','text-halo-color':'#dcece2','text-halo-width':1.8}},
  );
 return style;
}

export function fitVietnam(map:Map,duration=0){
 const el=map.getContainer(), box=el.getBoundingClientRect(), parent=el.parentElement;
 const bottom=parent?.querySelector('.destinations')?.getBoundingClientRect();
 const topElements=parent?.querySelectorAll('.map-title,.map-actions,.zoom-controls');
 let top=24;
 topElements?.forEach(node=>{const rect=node.getBoundingClientRect();if(rect.height)top=Math.max(top,rect.bottom-box.top+14);});
 const lower=bottom?.height?box.bottom-bottom.top+12:35;
 // The chatbot is outside this container; its width/height is already excluded.
 // Reserve text width on the east side as well as the existing overlay space.
 const camera=map.cameraForBounds([[102,7],[117.5,23.5]],{padding:{top:Math.min(top,box.height*0.42),bottom:Math.min(lower,box.height*0.3),left:25,right:box.width<500?65:100},maxZoom:6});
 if(camera)map.easeTo({...camera,padding:{top:0,bottom:0,left:0,right:0},duration});
}