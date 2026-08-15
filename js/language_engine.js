class FutureMindLanguage {

constructor(){

this.lang =
localStorage.getItem("futuremind_language") ||
localStorage.getItem("language") ||
"en";

this.data={};

}

async init(){

let saved =
localStorage.getItem("futuremind_language") ||
localStorage.getItem("language") ||
"en";

this.lang = saved;

await this.load();

this.applyDirection();

this.translate();

}

async load(){

let files=[
"common",
"home",
"store",
"checkout",
"products",
"remaining"
];

this.data={};

let loaded=false;

for(let file of files){

try{

let res =
await fetch(
`/lang/${this.lang}/${file}.json`
);

if(!res.ok){
continue;
}

let json =
await res.json();

this.data={
...this.data,
...json
};

loaded=true;

}catch(e){

console.log(
"Missing:",
file
);

}

}

/*
ROOT FALLBACK
Only used when the language folder
contains no translation files.
*/

if(!loaded){

try{

let res =
await fetch(`/lang/${this.lang}.json`);

if(res.ok){

let json =
await res.json();

this.data=json;

}

}catch(e){

console.log(
"Root language fallback missing:",
this.lang
);

}

}

}

t(key){

return this.data[key] ?? key;

}

translate(){

document
.querySelectorAll(
"[data-i18n],[data-lang]"
)
.forEach(el=>{

let key =
el.dataset.i18n ||
el.dataset.lang;

let value=this.t(key);

if(value !== key){

el.innerHTML=value;

}

});

document
.querySelectorAll(
"[data-lang-placeholder]"
)
.forEach(el=>{

let key =
el.getAttribute(
"data-lang-placeholder"
);

let value=this.t(key);

if(value !== key){

el.placeholder=value;

}

});

}

async change(lang){

this.lang=lang;

localStorage.setItem(
"futuremind_language",
lang
);

/*
Keep legacy storage synchronized
during migration.
*/

localStorage.setItem(
"language",
lang
);

await this.load();

this.applyDirection();

this.translate();

if(window.loadStoreProducts){

window.loadStoreProducts();

}

}

applyDirection(){

let rtl=[
"fa",
"ar"
];

document.documentElement.dir =
rtl.includes(this.lang)
?
"rtl"
:
"ltr";

document.documentElement.lang =
this.lang;

}

}

window.futuremindLanguage =
new FutureMindLanguage();

document.addEventListener(
"DOMContentLoaded",
()=>{
futuremindLanguage.init();
});
