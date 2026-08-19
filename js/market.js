let currentMarket = localStorage.getItem("market") || "global";

let currentMarketConfig = null;
let currentCurrency = null;
let currentPrice = null;

function setMarket(market){

    if (market !== "global" && market !== "iran"){
        console.warn("Unsupported market:", market);
        return;
    }

    currentMarket = market;

    localStorage.setItem("market", market);

    console.log("Market changed:", market);

    location.reload();
}


function getMarket(){

    return currentMarket;

}


function getCurrency(){

    return currentCurrency;

}


function getPrice(){

    return currentPrice;

}


async function loadMarket(){

    const response = await fetch(`/markets/${currentMarket}.json`);

    if (!response.ok){
        throw new Error(
            `Market config HTTP ${response.status}: ${currentMarket}`
        );
    }

    const marketConfig = await response.json();

    currentMarketConfig = marketConfig;
    currentCurrency = marketConfig.currency || null;

    /*
     * Market JSON intentionally contains market configuration only.
     * Product pricing remains owned by products/products.json.
     *
     * currentPrice is therefore nullable until a product price is supplied
     * through resolveMarketPrice().
     */
    currentPrice = null;

    console.log("Market Config:", marketConfig);

    return marketConfig;

}


function resolveMarketPrice(product){

    if (!product){
        currentPrice = null;
        return null;
    }

    let price = null;

    if (currentMarket === "iran"){
        price = product.iran_price;
    }else{
        price = product.price;
    }

    currentPrice = price;

    return price;

}
