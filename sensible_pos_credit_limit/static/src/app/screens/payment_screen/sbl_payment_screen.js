import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { AlertDialog, ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { patch } from "@web/core/utils/patch";


patch(PaymentScreen.prototype, {
    async addNewPaymentLine(paymentMethod) {
        await this.pos.updatePartnerAvailableCredit(this.currentOrder.partner_id);
        if(paymentMethod.sbl_credit_journal && !this.currentOrder.partner_id) {
            return this.dialog.add(AlertDialog, {
                title: _t("Customer Required"),
                body: _t(
                    "Please select a customer before adding a credit payment line."
                ),
            });
        }
        const totalAmountDue = await this.currentOrder.getDefaultAmountDueToPayIn(paymentMethod);
        const partnerAvailableCredit = this.pos.getPartnerAvailableCredit(this.currentOrder.partner_id);
        if (paymentMethod.sbl_credit_journal && totalAmountDue > partnerAvailableCredit) {
            await this.dialog.add(ConfirmationDialog, {
                title: _t("Credit Limit Exceeded?"),
                body: _t(
                    "The credit limit is exceeded. Do you want to use available credit and pay the rest by another payment method?"
                ),
                confirm: () => {
                    return this.currentOrder.add_credit_balance_paymentline(paymentMethod, partnerAvailableCredit);
                },
                cancel: () => {
                    this.deleteCreditPaymentLines();
                },
            })
        } else {
            return await super.addNewPaymentLine(...arguments);
        }
    },
    updateSelectedPaymentline(amount = false) {
        this.pos.updatePartnerAvailableCredit(this.currentOrder.partner_id);
        const payment_method = this.payment_methods_from_config[0];
        if(payment_method.sbl_credit_journal && !this.currentOrder.partner_id) {
            return this.dialog.add(AlertDialog, {
                title: _t("Customer Required"),
                body: _t(
                    "Please select a customer before adding a credit payment line."
                ),
            });
        }

        if (amount === false) {
            if (this.numberBuffer.get() === null) {
                amount = null;
            } else if (this.numberBuffer.get() === "") {
                amount = 0;
            } else {
                amount = this.numberBuffer.getFloat();
            }
        }
        const partnerAvailableCredit = this.pos.getPartnerAvailableCredit(this.currentOrder.partner_id);
        if (amount > partnerAvailableCredit) {
            this.dialog.add(ConfirmationDialog, {
                title: _t("Credit Limit Exceeded?"),
                body: _t(
                    `The credit limit is exceeded. Do you want to use available credit and pay the rest by another payment method?`
                ),
                confirm: () => {
                    return this.currentOrder.add_credit_balance_paymentline(payment_method, partnerAvailableCredit);
                },
                cancel: () => {
                    this.deleteCreditPaymentLines();
                },
            })
        }
        this.pos.updatePartnerAvailableCredit(this.currentOrder.partner_id);
        return super.updateSelectedPaymentline(...arguments);
    },
    deleteCreditPaymentLines() {
        const paymentLines = this.paymentLines.filter(
            (line) => line.payment_method_id?.sbl_credit_journal
        );
        for (const line of paymentLines) {
            this.deletePaymentLine(line.uuid);
        }
    }
});