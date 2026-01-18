/** @odoo-module */

import { registry } from "@web/core/registry";
import { Many2OneField } from "@web/views/fields/many2one/many2one_field";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillDestroy } from "@odoo/owl";

export class RfidTyreWidget extends Many2OneField {
    setup() {
        super.setup();
        this.busService = useService("bus_service");
        this.notification = useService("notification");

        // Channel to listen to
        this.channel = "rfid_scans";

        onWillStart(() => {
            this.busService.addChannel(this.channel);
            this.busService.subscribe(this.channel, this.onRfidNotification.bind(this));
        });

        onWillDestroy(() => {
            this.busService.unsubscribe(this.channel, this.onRfidNotification.bind(this));
        });
    }

    onRfidNotification(notification) {
        // Notification format: { type: 'rfid_notification', payload: { ... } }
        // or depending on Odoo version, it might be just payload if filtered by event listener?
        // Bus service usually emits events.

        // Let's assume standard bus structure: [notification]
        // Actually useService("bus_service") in recent Odoo handles it differently.
        // It provides .subscribe(channel, callback).

        // If notification matches our payload structure
        // Payload: { type: 'batch_scan', tyre_ids: [123, ...], ... }

        const payload = notification.payload || notification; // Robustness

        if (payload && payload.type === 'batch_scan' && payload.tyre_ids && payload.tyre_ids.length > 0) {
            const firstTyreId = payload.tyre_ids[0];

            // Auto-select this tyre
            // Many2One update expects: [id, displayName] or just Id if configured?
            // Usually we need the record to set it properly.
            // But we can try setting just ID and letting Many2One resolve it, or fetch name.

            // Simpler: Just trigger the update.
            console.log("RFID Auto-Select Tyre:", firstTyreId);

            // We need to pass an array [id] or [id, "Name"]
            // Since we don't have the name efficiently, let's try just searching/reading or optimistic update.
            // Many2OneField.update([id]) might trigger a read.

            // To be safe, let's just set the ID and let Odoo handle the rest.
            // Note: If we just pass [id], standard update might fail if it expects object.
            // Let's try to find the standard update signature.
            // It calls this.props.record.update({ [this.props.name]: value });

            // Let's try passing [id].
            this.props.update([firstTyreId]);

            // Visual feedback
            this.notification.add("RFID Scan detected! Tyre selected.", { type: "success" });
        }
    }
}

RfidTyreWidget.template = "web.Many2OneField";
RfidTyreWidget.components = {
    ...Many2OneField.components,
};
RfidTyreWidget.props = {
    ...Many2OneField.props,
};

export const rfidTyreWidget = {
    component: RfidTyreWidget,
    displayName: "RFID Tyre Selection",
    supportedTypes: ["many2one"],
    extractProps: Many2OneField.extractProps,
};

registry.category("fields").add("rfid_tyre_selection", rfidTyreWidget);
