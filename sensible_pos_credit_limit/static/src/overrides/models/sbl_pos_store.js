import { PosStore } from "@point_of_sale/app/services/pos_store";
import { patch } from "@web/core/utils/patch";


patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.updatePartnerAvailableCredit.bind(this);
    },
    async updatePartnerAvailableCredit(partner) {
        if(!partner) {
            return;
        }
        const partnerParent = this.getPartnerParent(partner);
        const sbl_available_credit = await this.data.call("res.partner", "get_available_credit", [
            partnerParent.id,
        ]);
        partnerParent.update({ sbl_available_credit });
        return [partnerParent];
    },
    getPartnerParent(partner) {
        if (partner && partner.parent_id) {
            partner = partner.parent_id;
        }
        return partner;
    },
    getPartnerAvailableCredit(partner) {
        if(!partner) {
            return 0;
        }
        let partnerParent = this.getPartnerParent(partner);
        return partnerParent.sbl_available_credit;
    },
});