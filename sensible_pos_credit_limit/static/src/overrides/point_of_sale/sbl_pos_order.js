import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";

patch(PosOrder.prototype, {
    add_credit_balance_paymentline(payment_method, amount) {
        this.assertEditable();
        if (this.electronicPaymentInProgress()) {
            return false;
        } else {
            const newPaymentLine = this.models["pos.payment"].create({
                pos_order_id: this,
                payment_method_id: payment_method,
            });
            this.selectPaymentline(newPaymentLine);
            newPaymentLine.setAmount(amount);

            if (
                (payment_method.payment_terminal && !this.isRefund) ||
                payment_method.payment_method_type === "qr_code"
            ) {
                newPaymentLine.setPaymentStatus("pending");
            }
            return newPaymentLine;
        }
    }
});
