import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentSelcom } from "@selcom_pos_terminal/app/payment_selcom";


register_payment_method("selcom", PaymentSelcom);


