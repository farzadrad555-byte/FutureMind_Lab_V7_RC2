/* R67_PRODUCT_ID_MAPPING_PATCH */
/* =========================================================================
   FutureMind Lab — Store Engine
   R65 PRICE INTEGRATION
   Canonical pricing source:
   /products/products.json
   ======================================================================= */

async function loadProducts(){

    const lang =
        localStorage.getItem("language") || "en";

    const market =
        localStorage.getItem("market") || "global";

    const languageResponse =
        await fetch(`/lang/${lang}/products.json`);

    if (!languageResponse.ok){
        throw new Error(
            "Language product source unavailable"
        );
    }

    const localizedProducts =
        await languageResponse.json();

    const canonicalResponse =
        await fetch("/products/products.json");

    if (!canonicalResponse.ok){
        throw new Error(
            "Canonical product source unavailable"
        );
    }

    const canonicalData =
        await canonicalResponse.json();

    const canonicalProducts =
        Array.isArray(canonicalData.products)
            ? canonicalData.products
            : [];

    const container =
        document.getElementById("products");

    if (!container){
        throw new Error(
            "Products container not found"
        );
    }

    container.innerHTML = "";

    /*
     * R143-E.11.5:
     * Normalize localized product source before resolving canonical products.
     *
     * Supported formats:
     *   1) { "product_id": {...}, ... }
     *   2) { "products": [{...}, {...}] }
     *   3) [{...}, {...}]
     */
    let localizedEntries = [];

    if (Array.isArray(localizedProducts)) {
        localizedEntries = localizedProducts.map((item, index) => [
            item?.id || item?._source_id || String(index),
            item || {}
        ]);
    } else if (
        localizedProducts &&
        Array.isArray(localizedProducts.products)
    ) {
        localizedEntries = localizedProducts.products.map((item, index) => [
            item?.id || item?._source_id || String(index),
            item || {}
        ]);
    } else if (
        localizedProducts &&
        typeof localizedProducts === "object"
    ) {
        localizedEntries = Object.entries(localizedProducts);
    }

    localizedEntries.forEach(([id, localized]) => {

        const safeLocalized =
            localized || {};

        const R67_PRODUCT_ID_MAP = {
    "hunter_x_v44": "hunter-x-v44",
    "science_teacher_ai": "science-ai-pack",
    "math_teacher_ai": "math-ai-pack",
    "futuremind_templates": "futuremind-templates",
    "ai_starter_pack": "futuremind-ai-starter-pack-v1",
    "ai_teacher_pack": "futuremind-ai-teacher-pack",
    "content_creator_pack": "futuremind-ai-content-creator-pack",
    "student_pack": "futuremind-ai-student-pack-v1",
    "research_assistant_pack": "futuremind-ai-research-assistant-v1",
    "business_assistant_pack": "futuremind-ai-business-assistant-v1"
};

const canonicalId =
    R67_PRODUCT_ID_MAP[id] || id;

const canonical =
    canonicalProducts.find(
        p => p.id === canonicalId
    );



        if (!canonical){
            return;
        }

        let price =
            market === "iran"
                ? canonical.iran_price
                : canonical.price;

        const currency =
            market === "iran"
                ? "IRR"
                : (canonical.currency || "USD");

        const numericPrice =
            Number(price);

        const displayPrice =
            Number.isFinite(numericPrice) &&
            numericPrice > 0
                ? numericPrice.toLocaleString()
                : "—";

        container.innerHTML += `
            <div class="card">

                <h2>${safeLocalized.title || canonical.name}</h2>

                <p>
                    ${safeLocalized.category || canonical.category || ""}
                </p>

                <p>
                    ${safeLocalized.description || canonical.description || ""}
                </p>

                <h2 class="product-price">
                    ${displayPrice}
                    ${displayPrice === "—" ? "" : " " + currency}
                </h2>

                <a
                    class="btn"
                    href="../pages/checkout.html?id=${canonicalId}"
                >
                    View Product
                </a>

            </div>
        `;

    });

}

document.addEventListener(
    "DOMContentLoaded",
    () => {
        loadProducts().catch(error => {
            console.error(
                "Store Engine Error:",
                error
            );
        });
    }
);
