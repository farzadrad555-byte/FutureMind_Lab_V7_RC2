
document.addEventListener("DOMContentLoaded",()=>{


const btn = document.getElementById("languageMenuBtn");
const menu = document.getElementById("languageMenu");


if(!btn || !menu){
    return;
}


btn.onclick = ()=>{
    menu.classList.toggle("show");
};



document.querySelectorAll(".lang-option").forEach(item=>{


item.onclick = async ()=>{


const lang = item.dataset.langCode;


if(window.futuremindLanguage){

    await futuremindLanguage.change(lang);

}



document.querySelectorAll(".lang-option")
.forEach(x=>{

x.innerHTML = x.innerHTML.replace("✓ ","");

});



item.innerHTML = "✓ " + item.innerHTML;



menu.classList.remove("show");


};


});


});
