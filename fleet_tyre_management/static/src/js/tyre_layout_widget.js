/** @odoo-module */

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

export class TyreLayoutWidget extends Component {
    static template = "fleet_tyre_management.TyreLayoutWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.action = useService("action");
        this.state = useState({
            data: this.parseData(this.props.record.data[this.props.name]),
        });

        onWillUpdateProps((nextProps) => {
            this.state.data = this.parseData(nextProps.record.data[nextProps.name]);
        });
    }

    parseData(jsonString) {
        try {
            return JSON.parse(jsonString || "{}");
        } catch (e) {
            console.error("Failed to parse tyre layout JSON:", e);
            return { units: [] };
        }
    }

    async onSlotClick(unit, slot) {
        if (!unit.vehicle_id || !slot.position_id) return;

        let action = {};
        const context = {
            default_vehicle_id: unit.vehicle_id,
            default_position_id: slot.position_id,
        };

        if (slot.tyre_id) {
            // Tyre is mounted -> Dismount / Inspect
            action = {
                name: "Tyre Operation",
                type: "ir.actions.act_window",
                res_model: "fleet.tyre.operation.wizard",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: {
                    ...context,
                    default_operation_type: 'dismount',
                    default_tyre_id: slot.tyre_id
                }
            };
        } else {
            // Empty slot -> Mount
            action = {
                name: "Mount Tyre",
                type: "ir.actions.act_window",
                res_model: "fleet.tyre.operation.wizard",
                view_mode: "form",
                views: [[false, "form"]],
                target: "new",
                context: {
                    ...context,
                    default_operation_type: 'mount'
                }
            };
        }

        await this.action.doAction(action, {
            onClose: async () => {
                await this.props.record.load(); // Refresh record
            }
        });
    }
}

export const tyreLayoutWidget = {
    component: TyreLayoutWidget,
    displayName: "Tyre Layout Visualization",
    supportedTypes: ["text"],
};

registry.category("fields").add("tyre_layout", tyreLayoutWidget);
