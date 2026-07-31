
let currentLang = localStorage.getItem("language") || "en";

async function loadLanguage(lang){

    const response = await fetch(`/lang/${lang}.json`);
    const texts = await response.json();

    document.querySelectorAll("[data-lang]").forEach(el=>{

        const key = el.getAttribute("data-lang");

        if(texts[key]){
            el.innerHTML = texts[key];
        }
        else{
            console.warn("Missing translation key:", key);
        }

    });

    
    document.querySelectorAll("[data-lang-placeholder]").forEach(el=>{

        const key = el.getAttribute("data-lang-placeholder");

        if(texts[key]){
            el.placeholder = texts[key];
        }
        else{
            console.warn("Missing placeholder translation key:", key);
        }

    });


    document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
    document.documentElement.lang = lang;

    localStorage.setItem("language", lang);
}


function changeLanguage(lang){
    loadLanguage(lang);
}


document.addEventListener("DOMContentLoaded",()=>{
    loadLanguage(currentLang);
});
