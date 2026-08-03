
document.addEventListener(
"DOMContentLoaded",
()=>{


const selector =
document.getElementById(
"languageSwitcher"
);



if(!selector)
return;



selector.value =
futuremindLanguage.lang;



selector.addEventListener(
"change",
async(e)=>{


await futuremindLanguage
.change(
e.target.value
);


});


});
