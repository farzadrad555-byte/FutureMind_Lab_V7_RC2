/*
 * FutureMind V7 RC2 — R52.67 language switcher
 * Global runtime contract.
 */

(function () {

    const LANGUAGE_CODES = [
        "ar","de","en","es","fa","fr","hi","id",
        "it","ja","ko","pt","tr","zh-CN"
    ];

    function initLanguageSwitcher() {

        const menu = document.getElementById("languageMenu");
        const btn = document.getElementById("languageMenuBtn");

        if (btn && menu) {
            btn.addEventListener("click", function (event) {
                event.stopPropagation();
                menu.classList.toggle("open");
                menu.classList.toggle("active");
            });
        }

        document.querySelectorAll(".lang-option").forEach(function (item) {

            const lang =
                item.dataset.lang ||
                item.getAttribute("data-lang") ||
                item.getAttribute("value");

            if (!lang || !LANGUAGE_CODES.includes(lang)) {
                return;
            }

            item.addEventListener("click", async function () {

                if (!window.futuremindLanguage) {
                    console.warn("FutureMind language engine is unavailable.");
                    return;
                }

                try {
                    await window.futuremindLanguage.change(lang);

                    document.querySelectorAll(".lang-option").forEach(function (x) {
                        x.classList.remove("active");
                    });

                    item.classList.add("active");

                    if (menu) {
                        menu.classList.remove("open");
                        menu.classList.remove("active");
                    }

                } catch (err) {
                    console.error("Language switch failed:", err);
                }
            });
        });

        // Explicit global contract.
        window.languageSwitcher = {
            languages: LANGUAGE_CODES.slice(),
            change: async function (lang) {
                if (!LANGUAGE_CODES.includes(lang)) {
                    throw new Error(`Unsupported language: ${lang}`);
                }

                if (!window.futuremindLanguage) {
                    throw new Error("FutureMind language engine unavailable");
                }

                return await window.futuremindLanguage.change(lang);
            }
        };
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initLanguageSwitcher);
    } else {
        initLanguageSwitcher();
    }

})();
