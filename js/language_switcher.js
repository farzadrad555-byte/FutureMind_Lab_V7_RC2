/*
 * FutureMind V7 RC2 — R69.8 language switcher
 * Professional active-language runtime contract.
 */

(function () {

    const LANGUAGE_CODES = [
        "ar", "de", "en", "es", "fa", "fr", "hi",
        "id", "it", "ja", "ko", "pt", "tr", "zh-CN"
    ];

    function isSupportedLanguage(lang) {
        return LANGUAGE_CODES.includes(lang);
    }

    function getOptionLanguage(item) {
        return (
            item.dataset.language ||
            item.getAttribute("data-language") ||
            item.getAttribute("value") ||
            ""
        );
    }

    function setActiveLanguage(lang) {

        if (!isSupportedLanguage(lang)) {
            lang = "en";
        }

        document.querySelectorAll(".lang-option").forEach(function (item) {

            const code = getOptionLanguage(item);
            const active = code === lang;

            item.classList.toggle("active", active);

            item.setAttribute(
                "aria-selected",
                active ? "true" : "false"
            );
        });
    }

    function getInitialLanguage() {

        try {

            if (
                window.futuremindLanguage &&
                isSupportedLanguage(window.futuremindLanguage.lang)
            ) {
                return window.futuremindLanguage.lang;
            }

            const persisted =
                localStorage.getItem("futuremind_language");

            if (isSupportedLanguage(persisted)) {
                return persisted;
            }

        } catch (err) {
            console.warn(
                "Could not read persisted language:",
                err
            );
        }

        return "en";
    }

    // ========================================================
    // R143-D.5 — GLOBAL LANGUAGE UI
    // Canonical 14-language UI mounted centrally.
    // Idempotent: safe when pages already contain legacy UI.
    // Does NOT modify FutureMindLanguage engine.
    // ========================================================

    function mountGlobalLanguageUI() {

        const MOUNT_ID = "futuremind-global-language-ui";

        // Existing page-owned language UI → reuse it.
        const existingButton = document.getElementById("languageMenuBtn");
        const existingMenu = document.getElementById("languageMenu");

        if (existingButton && existingMenu) {
            const existingRoot = existingButton.closest(".language-switcher");

            if (existingRoot) {
                return existingRoot;
            }
        }

        // Already mounted dynamically → do nothing.
        const existingMount = document.getElementById(MOUNT_ID);

        if (existingMount) {
            return existingMount;
        }

        const host = document.createElement("div");

        host.id = MOUNT_ID;
        host.className = "language-switcher";

        host.innerHTML = `
            <button
                id="languageMenuBtn"
                class="lang-btn"
                type="button"
                aria-haspopup="true"
                aria-expanded="false"
            >
                🌐 Language ▾
            </button>

            <div
                id="languageMenu"
                class="language-menu"
                role="menu"
            >
                <button class="lang-option" data-language="en">🇺🇸 English</button>
                <button class="lang-option" data-language="fa">🇮🇷 فارسی</button>
                <button class="lang-option" data-language="ar">🇸🇦 العربية</button>
                <button class="lang-option" data-language="de">🇩🇪 Deutsch</button>
                <button class="lang-option" data-language="es">🇪🇸 Español</button>
                <button class="lang-option" data-language="fr">🇫🇷 Français</button>
                <button class="lang-option" data-language="hi">🇮🇳 हिन्दी</button>
                <button class="lang-option" data-language="id">🇮🇩 Indonesia</button>
                <button class="lang-option" data-language="it">🇮🇹 Italiano</button>
                <button class="lang-option" data-language="ja">🇯🇵 日本語</button>
                <button class="lang-option" data-language="ko">🇰🇷 한국어</button>
                <button class="lang-option" data-language="pt">🇵🇹 Português</button>
                <button class="lang-option" data-language="tr">🇹🇷 Türkçe</button>
                <button class="lang-option" data-language="zh-CN">🇨🇳 中文</button>
            </div>
        `;

        // R98-L2P — mount global language UI inside the site navigation
        // when available. This keeps the language control in the top UI
        // on mobile instead of placing it at the end of the document.
        //
        // Fallback to body is preserved for pages without navigation.
        const navigationHost = document.querySelector(".navigation");

        if (navigationHost) {
            navigationHost.appendChild(host);
        } else {
            document.body.appendChild(host);
        }

        return host;
    }


    function initLanguageSwitcher() {

        // R143-D.5 — mount canonical global language UI first.
        mountGlobalLanguageUI();

        const menu =
            document.getElementById("languageMenu");

        const btn =
            document.getElementById("languageMenuBtn");

        if (btn && menu) {

            btn.addEventListener("click", function (event) {

                event.stopPropagation();

                menu.classList.toggle("show");
            });
        }

        document.querySelectorAll(".lang-option")
            .forEach(function (item) {

                const lang = getOptionLanguage(item);

                if (!isSupportedLanguage(lang)) {
                    return;
                }

                item.addEventListener(
                    "click",
                    async function () {

                        if (!window.futuremindLanguage) {

                            console.warn(
                                "FutureMind language engine is unavailable."
                            );

                            return;
                        }

                        try {

                            await window.changeLanguage(lang);

                            setActiveLanguage(lang);

                            if (menu) {
                                menu.classList.remove("show");
                            }

                        } catch (err) {

                            console.error(
                                "Language switch failed:",
                                err
                            );
                        }
                    }
                );
            });

        // Restore persisted/current language exactly once.
        setActiveLanguage(getInitialLanguage());

        // Explicit global contract.
        window.languageSwitcher = {

            languages: LANGUAGE_CODES.slice(),

            change: async function (lang) {

                if (!isSupportedLanguage(lang)) {

                    throw new Error(
                        `Unsupported language: ${lang}`
                    );
                }

                if (!window.futuremindLanguage) {

                    throw new Error(
                        "FutureMind language engine unavailable"
                    );
                }

                const result =
                    await window.changeLanguage(lang);

                setActiveLanguage(lang);

                return result;
            }
        };
    }

    if (document.readyState === "loading") {

        document.addEventListener(
            "DOMContentLoaded",
            initLanguageSwitcher
        );

    } else {

        initLanguageSwitcher();
    }

})();

/* ============================================================================
   R98-L2AA — MOBILE VIEWPORT-FIXED LANGUAGE POSITION
   CSS is injected safely from JavaScript.
   ============================================================================ */

(function () {
    "use strict";

    const STYLE_ID = "futuremind-language-mobile-fixed-style";

    if (document.getElementById(STYLE_ID)) {
        return;
    }

    const style = document.createElement("style");
    style.id = STYLE_ID;

    style.textContent = `
@media (max-width: 600px) {
    #futuremind-global-language-ui.language-switcher {
        position: fixed !important;
        top: 8px !important;
        right: 8px !important;
        left: auto !important;
        bottom: auto !important;
        margin: 0 !important;
        z-index: 2147483647 !important;
    }

    #futuremind-global-language-ui.language-switcher .language-menu {
        position: absolute !important;
        top: calc(100% + 8px) !important;
        right: 0 !important;
        left: auto !important;
        bottom: auto !important;
        z-index: 2147483647 !important;
    }
}
`;

    (document.head || document.documentElement).appendChild(style);
})();
