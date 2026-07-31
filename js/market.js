
let currentMarket = localStorage.getItem("market") || "global";

function setMarket(market){

    currentMarket = market;

    localStorage.setItem("market", market);

    console.log("Market changed:", market);

    location.reload();
}


function getMarket(){

    return currentMarket;

}


async function loadMarket(){

    const response = await fetch(`/markets/${currentMarket}.json`);

    const marketConfig = await response.json();

    console.log("Market Config:", marketConfig);

    return marketConfig;

}
