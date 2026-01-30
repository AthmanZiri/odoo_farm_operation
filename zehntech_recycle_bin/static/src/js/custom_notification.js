/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(FormController.prototype, {
    async deleteRecord() {
        const dialogService = this.env.services.dialog;
        const notificationService = this.env.services.notification;
        console.log("Delete record called!");

        if (!dialogService || !notificationService) {
            console.error("Dialog or Notification service is not available.");
            return;
        }

        dialogService.add(ConfirmationDialog, {
            body: _t("Are you sure you want to delete this record?"),
            confirm: async () => {
                try {
                    await this.model.root.delete();
                    if (!this.model.root.resId) {
                        this.env.config.historyBack();
                        console.log("Record deleted successfully!");
                    }
                    notificationService.add(
                        _t("Record deleted successfully!"),
                        { title: _t("Success"), type: 'success' }
                    );
                } catch (error) {
                    console.error("Error deleting record:", error);
                    notificationService.add(
                        _t("Record required by another model. Consider archiving instead."),
                        { title: _t("Info"), type: 'info' }
                    );
                }
            },
            cancel: () => {
                console.log("Deletion canceled.");
            },
        });
    },
});
