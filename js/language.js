let currentLang = localStorage.getItem("language") || "en";

async function loadLanguage(lang){

    let texts = {};

    try {

        const files = [
            "common.json",
            "home.json",
            "products.json",
            "store.json",
            "checkout.json",
            "remaining.json"
        ];

        let folderLoaded = false;

        for(const file of files){

            const response = await fetch(`/lang/${lang}/${file}`);

            if(response.ok){

                const data = await response.json();

                texts = {
                    ...texts,
                    ...data
                };

                folderLoaded = true;
            }
        }


        if(!folderLoaded){

            const rootResponse = await fetch(`/lang/${lang}.json`);

            if(rootResponse.ok){

                texts = await rootResponse.json();

            }
        }


        document.querySelectorAll("[data-i18n],[data-lang]").forEach(el=>{

            const key = el.getAttribute("data-i18n") || el.getAttribute("data-lang");

            if(texts[key]){

                el.innerHTML = texts[key];

            }

        });


        document.querySelectorAll("[data-lang-placeholder]").forEach(el=>{

            const key = el.getAttribute("data-lang-placeholder");

            if(texts[key]){

                el.placeholder = texts[key];

            }

        });


        document.documentElement.dir = lang === "fa" ? "rtl" : "ltr";
        document.documentElement.lang = lang;

        localStorage.setItem("language", lang);


    } catch(error){

        console.error("Language loading error:", error);

    }

}


function changeLanguage(lang){
    loadLanguage(lang);
}


window.legacyLanguage = {
    change: changeLanguage
};


document.addEventListener("DOMContentLoaded",()=>{
    loadLanguage(currentLang);
});
