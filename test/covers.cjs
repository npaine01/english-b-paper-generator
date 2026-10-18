// A cover switch must change the cover without changing the question body.
const fs = require('node:fs');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const path = require('node:path');
const html = fs.readFileSync(path.join(__dirname, '../ui/index.html'), 'utf8');
const source = html.slice(html.indexOf('const INSTRUCTIONS ='), html.indexOf('/* ═══ rendering'));
const ctx = vm.createContext({load: () => null, modelComment: () => []});
vm.runInContext(source, ctx);
const paper = {kind:'reading', session:'QDHS', date:'18 October 2026', target:40,
  items:[{t:'text',label:'A',title:'Garden'}, {t:'short',stem:'Why?',answer:'Food'}]};
ctx.fixture = paper;
vm.runInContext('paper = fixture', ctx);
const generic = vm.runInContext('buildTex()', ctx);
assert.match(generic, /\\ibcover\n/);
ctx.fixture = {...paper, cover:'internal', coverDetails:{academic:'2026–2027 Academic Year | First Term',
  exam:'Midterm Examination', grade:'G11', duration:'75 mins'}};
vm.runInContext('paper = fixture', ctx);
const internal = vm.runInContext('buildTex()', ctx);
assert.match(internal, /\\usepackage\{qdhscover\}/);
assert.match(internal, /\\qdhscover/);
assert.match(internal, /Midterm Examination/);
assert.match(internal, /75 mins/);
assert.doesNotMatch(internal, /Write your session number/);
const body = s => s.slice(s.indexOf('\\ibtextheading'));
assert.equal(body(internal), body(generic));
for (const kind of ['listening','paper1']) {
  ctx.fixture = {...paper, kind, cover:'internal', items:[]};
  vm.runInContext('paper = fixture', ctx);
  const tex = vm.runInContext('buildTex()', ctx);
  assert.match(tex, /\\qdhscover/);
  assert.match(tex, kind === 'paper1' ? /90 mins/ : /60 mins/);
}
if (process.argv[2]) fs.writeFileSync(process.argv[2], internal);
console.log('Cover selection, metadata, instructions and unchanged question body: passed');
