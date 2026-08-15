
async function submitOrder(){

    console.log("SUBMIT CLICKED");
    console.log("PRODUCT:", window.selectedProduct);

    if(!window.productReady || !window.selectedProduct){
        alert(window.futuremindLanguage?.t("checkout_loading") || "Please wait, product is loading...");
        return;
    }

    const name = document.getElementById("name").value;
    const email = document.getElementById("email").value;

    if(!name || !email){
        alert(window.futuremindLanguage?.t("checkout_name_email") || "Please enter your name and email");
        return;
    }

    const market = getMarket();

    const marketData = window.selectedProduct.markets[market];


    const orderData = {

        name: name,
        email: email,

        market: market,

        product: window.selectedProduct.name,
        product_id: window.selectedProduct.id,

        amount: marketData.price,

        currency: marketData.currency,

        payment_method: marketData.payment

    };


    try{

        const response = await fetch("/api/order",{

            method:"POST",

            headers:{
                "Content-Type":"application/json"
            },

            body:JSON.stringify(orderData)

        });


        const data = await response.json();


        if(data.status === "success"){

            localStorage.setItem(
                "order_id",
                data.order_id
            );


            const payment = await fetch("/api/payment/confirm",{

                method:"POST",

                headers:{
                    "Content-Type":"application/json"
                },

                body:JSON.stringify({
                    order_id:data.order_id
                })

            });


            const paymentData = await payment.json();


            if(paymentData.status === "success"){

                localStorage.setItem(
                    "download_portal",
                    paymentData.download_portal
                );

                localStorage.setItem(
                    "payment_status",
                    paymentData.payment_status
                );

            }


            const token =
            paymentData.download.token;

            window.location.href =
            "order_success.html?token=" + token;

        }
        else{

            alert(window.futuremindLanguage?.t("checkout_order_failed") || "Order failed");

        }

    }

    catch(error){

        console.log(error);

        alert(window.futuremindLanguage?.t("checkout_connection_error") || "Connection error");

    }

}
