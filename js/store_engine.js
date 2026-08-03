
async function loadStoreProducts(){

    const lang =
    futuremindLanguage.lang;


    const response =
    await fetch(
    `/lang/${lang}/products.json`
    );


    const products =
    await response.json();


    const container =
    document.getElementById("products");


    if(!container)
    return;


    container.innerHTML="";


    Object.keys(products).forEach(id=>{


        const p =
        products[id];


        container.innerHTML += `

        <div class="card">


        <h2>${p.title}</h2>


        <h3>
        ${p.category}
        </h3>


        <p>
        ${p.description}
        </p>


        <a class="btn"
        href="checkout.html?id=${id}">
        View Product
        </a>


        </div>

        `;


    });


}


window.loadStoreProducts = loadStoreProducts;


document.addEventListener(
"DOMContentLoaded",
()=>{


if(window.futuremindLanguage){

    loadStoreProducts();

}


});
