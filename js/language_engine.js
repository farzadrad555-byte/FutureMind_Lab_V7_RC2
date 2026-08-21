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

        // R128: in-memory bundle cache.
        // Successful bundles are fetched once per page session.
        if (!this._bundleCache) {
            this._bundleCache = new Map();
        }

        if (this._bundleCache.has(lang)) {
            return this._bundleCache.get(lang);
        }

        const bundle = {};

        // ---------------------------------------------------------------
        // 1. Folder-based translation bundles
        // ---------------------------------------------------------------
        for (const file of this.files) {
            const data = await this._loadFile(lang, file);
            Object.assign(bundle, data);
        }

        // ---------------------------------------------------------------
        // 2. Root language baseline
        // ---------------------------------------------------------------
        let rootData = {};

        if (lang === "en" || lang === "fa") {
            rootData = await this._loadRootLanguageFile(lang);
        }

        // Root data fills ONLY missing keys.
        for (const [key, value] of Object.entries(rootData)) {
            if (!Object.prototype.hasOwnProperty.call(bundle, key)) {
                bundle[key] = value;
            }
        }

        // Cache only after successful completion.
        this._bundleCache.set(lang, bundle);

        return bundle;
    }

    async _loadRootLanguageFile(lang) {
        const url = `/lang/${lang}.json`;

        try {
            const res = await fetch(url, { cache: "no-store" });

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}`);
            }

            const data = await res.json();

            if (!data || typeof data !== "object" || Array.isArray(data)) {
                throw new Error("Invalid root translation object");
            }

            return data;
        } catch (err) {
            console.warn(
                `FutureMind root translation load failed: ${lang}.json`,
                err
            );

            return {};
        }
    }

    async loadLanguage(lang = this.lang) {
        this.lang = lang;

        // ---------------------------------------------------------------
        // Primary language
        // ---------------------------------------------------------------
        const primary = await this._loadLanguageBundle(this.lang);

        // ---------------------------------------------------------------
        // English authoritative fallback
        //
        // English root + English sub-bundles are both loaded.
        // English fills ONLY missing keys.
        // ---------------------------------------------------------------
        if (this.lang !== this.defaultLanguage) {
            const fallback =
                await this._loadLanguageBundle(this.defaultLanguage);

            this.translations = Object.assign({}, fallback, primary);
        } else {
            this.translations = primary;
        }

        this.loaded = true;

        document.documentElement.lang = this.lang;

        if (this.lang === "fa" || this.lang === "ar") {
            document.documentElement.dir = "rtl";
        } else {
            document.documentElement.dir = "ltr";
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

        // R84.7-C3:
        // Backward compatibility for existing data-lang markup.

        document.querySelectorAll("[data-i18n], [data-lang]").forEach(el => {
            const key =
                el.getAttribute("data-i18n") ||
                el.getAttribute("data-lang");

            if (!key) return;

            const value = this.t(key);

            if (value !== undefined && value !== null) {
                el.textContent = value;
            }
        });

        document.querySelectorAll(
            "[data-i18n-placeholder], [data-lang-placeholder]"
        ).forEach(el => {
            const key =
                el.getAttribute("data-i18n-placeholder") ||
                el.getAttribute("data-lang-placeholder");

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
