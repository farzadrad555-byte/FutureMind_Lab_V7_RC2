/* FutureMind V7 RC2 — Legacy API Compatibility Layer */

(function(){

    "use strict";

    const LEGACY_STORAGE_KEY = "language";
    const MODERN_STORAGE_KEY = "futuremind_language";

    function syncLegacyStorage(lang){

        if(!lang){
            return;
        }

        try{
            localStorage.setItem(
                LEGACY_STORAGE_KEY,
                lang
            );
        }catch(e){
            console.warn(
                "Legacy language storage sync failed:",
                e
            );
        }
    }

    function getLegacyLanguage(){

        try{
            return localStorage.getItem(
                LEGACY_STORAGE_KEY
            );
        }catch(e){
            return "en";
        }
    }

    function getModernLanguage(){

        try{
            return localStorage.getItem(
                MODERN_STORAGE_KEY
            );
        }catch(e){
            return null;
        }
    }

    function waitForModernOwner(
        timeout=10000,
        interval=25
    ){

        return new Promise((resolve,reject)=>{

            const started = Date.now();

            function check(){

                if(
                    window.futuremindLanguage &&
                    typeof window.futuremindLanguage.change === "function"
                ){
                    resolve(
                        window.futuremindLanguage
                    );
                    return;
                }

                if(
                    Date.now() - started >= timeout
                ){
                    reject(
                        new Error(
                            "FutureMindLanguage owner was not initialized in time."
                        )
                    );
                    return;
                }

                setTimeout(
                    check,
                    interval
                );
            }

            check();
        });
    }

    async function delegateChange(lang){

        if(!lang){
            lang = getLegacyLanguage();
        }

        const owner =
            await waitForModernOwner();

        await owner.change(lang);

        syncLegacyStorage(lang);

        return owner;
    }

    async function loadLanguage(lang){

        return delegateChange(
            lang || getLegacyLanguage()
        );
    }

    async function changeLanguage(lang){

        return delegateChange(lang);
    }

    window.legacyLanguage = {
        change: changeLanguage
    };

    window.loadLanguage =
        loadLanguage;

    window.changeLanguage =
        changeLanguage;

    document.addEventListener(
        "DOMContentLoaded",
        async ()=>{

            try{

                const legacyLang =
                    getLegacyLanguage();

                const modernLang =
                    getModernLanguage();

                const initialLang =
                    modernLang ||
                    legacyLang ||
                    "en";

                await delegateChange(
                    initialLang
                );

            }catch(error){

                console.error(
                    "Legacy compatibility initialization failed:",
                    error
                );

            }

        }
    );

})();
