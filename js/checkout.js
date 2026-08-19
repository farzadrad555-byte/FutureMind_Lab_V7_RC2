
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
            /*
             * R100-F.1
             * SECURITY-FIRST FAIL-CLOSED BOUNDARY
             *
             * The browser does not possess server-verifiable
             * payment evidence at this stage.
             *
             * Therefore this client MUST NOT mark an order paid,
             * request a download token, or redirect to download
             * after order creation alone.
             */

            localStorage.setItem(
                "order_id",
                data.order_id
            );

            localStorage.setItem(
                "payment_status",
                "PENDING"
            );

            console.log(
                "ORDER CREATED — PAYMENT PENDING:",
                data.order_id
            );

            alert(
                "Order created successfully.\n\n" +
                "Order ID: " + data.order_id + "\n\n" +
                "Payment verification is required before download."
            );

            return;


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
