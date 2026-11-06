import {createRequire} from 'node:module';
import {dirname,join} from 'node:path';
import {fileURLToPath} from 'node:url';
const here=dirname(fileURLToPath(import.meta.url));
// Reuse the host project's installed packages; do not download dependencies.
const require=createRequire(process.env.PAPER_DEMO_NODE_MODULES?join(process.env.PAPER_DEMO_NODE_MODULES,'../package.json'):import.meta.url);
const esbuild=require('esbuild'),modules=dirname(dirname(require.resolve('react/package.json')));
await esbuild.build({entryPoints:[join(here,'browser_entry.tsx')],bundle:true,minify:true,platform:'browser',format:'iife',
 target:['chrome110'],outfile:join(here,'browser.js'),nodePaths:[modules],define:{'process.env.NODE_ENV':'"production"'}});
console.log('Built reference_realization/browser.js from local TSX.');
