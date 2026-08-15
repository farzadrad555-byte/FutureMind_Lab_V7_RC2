/*
 * FutureMind V7 RC2 — R52.67 language engine
 * Contract:
 *   - six folder JSON resources
 *   - deterministic load order
 *   - English fallback
 *   - no JSON mutation
 *   - safe runtime failure handling
 */

class FutureMindLanguage {

    constructor(options = {}) {
        this.defaultLanguage = options.defaultLanguage || "en";
        this.lang = options.lang || localStorage.getItem("futuremind_language") || this.defaultLanguage;

        this.files = [
            "common",
            "home",
            "store",
            "checkout",
            "products",
            "remaining"
        ];

        this.translations = {};
        this.loaded = false;
    }

    async _loadFile(lang, file) {
        const url = `/lang/${lang}/${file}.json`;

        try {
            const res = await fetch(url, { cache: "no-store" });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();

            if (!data || typeof data !== "object" || Array.isArray(data)) {
                throw new Error("Invalid translation object");
            }

            return data;
        } catch (err) {
            console.warn(`FutureMind translation load failed: ${lang}/${file}.json`, err);
            return {};
        }
    }

    async _loadLanguageBundle(lang) {
        const bundle = {};

        for (const file of this.files) {
            const data = await this._loadFile(lang, file);
            Object.assign(bundle, data);
        }

        return bundle;
    }

    async loadLanguage(lang = this.lang) {
        this.lang = lang;

        const primary = await this._loadLanguageBundle(this.lang);

        // English is the authoritative fallback baseline.
        if (this.lang !== this.defaultLanguage) {
            const fallback = await this._loadLanguageBundle(this.defaultLanguage);

            // English fills ONLY missing keys.
            this.translations = Object.assign({}, fallback, primary);
        } else {
            this.translations = primary;
        }

        this.loaded = true;

        document.documentElement.setAttribute("lang", this.lang);

        if (this.lang === "fa" || this.lang === "ar") {
            document.documentElement.setAttribute("dir", "rtl");
        } else {
            document.documentElement.setAttribute("dir", "ltr");
        }

        this.applyTranslations();

        return this.translations;
    }

    async change(lang) {
        if (!lang || lang === this.lang && this.loaded) {
            return this.translations;
        }

        localStorage.setItem("futuremind_language", lang);

        return await this.loadLanguage(lang);
    }

    t(key, fallback = "") {
        if (Object.prototype.hasOwnProperty.call(this.translations, key)) {
            return this.translations[key];
        }

        return fallback || key;
    }

    applyTranslations() {
        document.querySelectorAll("[data-i18n]").forEach(el => {
            const key = el.getAttribute("data-i18n");
            if (!key) return;

            const value = this.t(key);

            if (value !== undefined && value !== null) {
                el.textContent = value;
            }
        });

        document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (!key) return;

            const value = this.t(key);

            if (value !== undefined && value !== null) {
                el.setAttribute("placeholder", value);
            }
        });

        document.querySelectorAll("[data-i18n-title]").forEach(el => {
            const key = el.getAttribute("data-i18n-title");
            if (!key) return;

            const value = this.t(key);

            if (value !== undefined && value !== null) {
                el.setAttribute("title", value);
            }
        });

        if (typeof window.loadStoreProducts === "function") {
            try {
                window.loadStoreProducts();
            } catch (e) {
                console.warn("loadStoreProducts failed after language change:", e);
            }
        }
    }
}

window.FutureMindLanguage = FutureMindLanguage;

window.futuremindLanguage =
    window.futuremindLanguage ||
    new FutureMindLanguage();

window.languageSwitcher =
    window.languageSwitcher ||
    window.futuremindLanguage;

window.language =
    window.language ||
    window.futuremindLanguage;
