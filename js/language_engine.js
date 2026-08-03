
class FutureMindLanguage {

constructor(){

this.lang="en";
this.data={};

}


async init(){

let saved =
localStorage.getItem(
"futuremind_language"
);


this.lang =
saved || "en";


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
"products"
];


this.data={};


for(let file of files){


try{

let res =
await fetch(
`/lang/${this.lang}/${file}.json`
);


let json =
await res.json();


this.data={
...this.data,
...json
};


}catch(e){

console.log(
"Missing:",
file
);

}


}


}



t(key){

return this.data[key] || key;

}



translate(){


document
.querySelectorAll(
"[data-i18n]"
)
.forEach(el=>{


let key =
el.dataset.i18n;


el.innerText =
this.t(key);


});


}



async change(lang){


this.lang=lang;


localStorage.setItem(
"futuremind_language",
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


}

}



window.futuremindLanguage =
new FutureMindLanguage();


document.addEventListener(
"DOMContentLoaded",
()=>{

futuremindLanguage.init();

});
