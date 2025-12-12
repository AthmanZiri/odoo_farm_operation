import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { onMounted } from "@odoo/owl";

patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        onMounted(() => {
            this.pos.updatePartnerAvailableCredit(this.pos.getPartnerParent(this.props.partner));
        });
    },
    get partnerAvailableCredit() {
        return this.pos.getPartnerAvailableCredit(this.props.partner);
    },
});
