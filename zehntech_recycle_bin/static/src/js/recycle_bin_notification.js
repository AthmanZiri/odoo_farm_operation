/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ListController } from "@web/views/list/list_controller";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";
import { sprintf } from "@web/core/utils/strings";

patch(ListController.prototype, {
    get deleteConfirmationDialogProps() {
        const root = this.model.root;
        const recordCount = root.isDomainSelected ? root.count : root.selection.length;
        let body = _t("Are you sure you want to delete this record?");
        if (recordCount > 1) {
            body = sprintf(
                _t("Are you sure you want to delete these %s records?"),
                recordCount
            );
        }

        return {
            title: _t("Delete Confirmation"),
            body,
            confirmLabel: _t("Delete"),
            confirm: async () => {
                try {
                    // Perform the delete operation
                    await root.deleteRecords();

                    // Notify the user of successful deletion (with the number of records)
                    const notificationService = this.env.services.notification;
                    notificationService.add(
                        sprintf(_t("%s records have been successfully deleted."), recordCount), // Changed line
                        { title: _t("Success"), type: "success" }
                    );
                } catch (error) {
                    // Handle any errors during deletion
                    const notificationService = this.env.services.notification;
                    notificationService.add(
                        _t("Record required by another model. Consider archiving instead."),
                        { title: _t("Info"), type: 'info' }
                    );
                }
            },
            cancel: () => {},
            cancelLabel: _t("Cancel"),
        };
    },

    async onDeleteSelectedRecords() {
        this.dialogService.add(ConfirmationDialog, this.deleteConfirmationDialogProps);
    },
});
