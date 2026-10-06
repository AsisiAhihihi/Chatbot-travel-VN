import {defineConfig} from 'vite';
export default defineConfig({
 base:process.env.VITE_BASE_PATH || '/',
 optimizeDeps:{exclude:['maplibre-gl']},
 build:{rollupOptions:{output:{manualChunks(id){
  const path=id.replace(/\\/g,'/');
  if(path.includes('/node_modules/maplibre-gl/'))return 'maplibre';
  if(/\/node_modules\/(react|react-dom|scheduler)\//.test(path))return 'react-vendor';
 }}}},
});