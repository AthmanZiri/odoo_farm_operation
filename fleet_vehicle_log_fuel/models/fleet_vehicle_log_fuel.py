# Copyright 2022 ForgeFlow S.L.  <https://www.forgeflow.com>
# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class FleetVehicleLogFuel(models.Model):
    _name = "fleet.vehicle.log.fuel"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "service_type_id"
    _description = "Fuel log for vehicles"

    active = fields.Boolean(default=True)
    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        "Vehicle",
        required=True,
        help="Vehicle concerned by this log",
    )
    product_id = fields.Many2one("product.product", string="Fuel Product")
    location_id = fields.Many2one(
        "stock.location", string="Source Location", domain="[('usage', '=', 'internal')]"
    )
    location_dest_id = fields.Many2one("stock.location", string="Destination Location")
    stock_move_id = fields.Many2one("stock.move", "Stock Move", readonly=True)
    amount = fields.Monetary("Cost")
    description = fields.Char()
    odometer_id = fields.Many2one(
        "fleet.vehicle.odometer",
        "Odometer",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer = fields.Float(
        compute="_compute_odometer",
        store=True,
        inverse="_inverse_odometer",
        string="Odometer Value",
        help="Odometer measure of the vehicle at the moment of this log",
    )
    odometer_unit = fields.Selection(related="vehicle_id.odometer_unit", string="Unit")
    date = fields.Date(
        help="Date when the cost has been executed",
        default=fields.Date.context_today,
        compute="_compute_date",
        store=True,
        readonly=False,
        precompute=True,
    )
    company_id = fields.Many2one(
        "res.company", "Company", default=lambda self: self.env.company
    )
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    purchaser_id = fields.Many2one(
        "res.partner",
        string="Driver",
        compute="_compute_purchaser_id",
        store=True,
    )
    # Related vehicle fields exposed for reporting / grouping ("per fleet" and
    # "all fleets" utilization analyses are driven from these dimensions).
    model_id = fields.Many2one(
        "fleet.vehicle.model",
        related="vehicle_id.model_id",
        store=True,
        string="Model",
    )
    category_id = fields.Many2one(
        "fleet.vehicle.model.category",
        related="vehicle_id.category_id",
        store=True,
        string="Fleet Category",
    )
    tag_ids = fields.Many2many(
        related="vehicle_id.tag_ids",
        string="Tags",
    )
    fuel_type = fields.Selection(
        related="vehicle_id.fuel_type",
        store=True,
        string="Fuel Type",
    )
    inv_ref = fields.Char("Vendor Reference")
    vendor_id = fields.Many2one("res.partner", "Vendor")
    notes = fields.Text()
    service_type_id = fields.Many2one(
        "fleet.service.type",
        "Service Type",
        required=True,
        default=lambda self: self.env.ref(
            "fleet.type_service_refueling", raise_if_not_found=False
        ),
    )
    state = fields.Selection(
        [
            ("todo", "To Do"),
            ("running", "Running"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        default="todo",
        string="Stage",
    )
    liter = fields.Float()
    price_per_liter = fields.Float()
    service_id = fields.Many2one(
        comodel_name="fleet.vehicle.log.services", readonly=True, copy=False
    )
    # New Fields
    filler_id = fields.Many2one("res.partner", string="Filler")
    job = fields.Char(string="Job")
    pump_meter = fields.Float(string="Pump Meter")
    physical_pump_reading = fields.Float(string="Physical Pump Reading")
    date_time = fields.Datetime(string="Date & Time", default=fields.Datetime.now)

    # Computed stats
    prev_odometer = fields.Float(
        string="Prev Odometer", compute="_compute_prev_log_stats", store=True
    )
    prev_date = fields.Date(
        string="Prev Date", compute="_compute_prev_log_stats", store=True
    )
    has_prev_log = fields.Boolean(
        compute="_compute_prev_log_stats",
        store=True,
        help="True when a previous fuel log exists for the vehicle, so that "
        "distance and consumption can be derived meaningfully.",
    )
    distance = fields.Float(
        string="Distance", compute="_compute_consumption", store=True
    )
    consumption_rate = fields.Float(
        string="Consumption Rate", compute="_compute_consumption", store=True,
        help="Litres consumed per unit of distance/time since the previous log "
        "(L/Hr for machinery, L/km for road vehicles).",
    )
    avg_consumption_rate = fields.Float(
        string="Average CR",
        compute="_compute_avg_consumption",
        store=True,
        help="Lifetime average consumption rate for the vehicle "
        "(sum(litres) / sum(distance) across all non-cancelled fuel logs).",
    )

    @api.depends("date_time")
    def _compute_date(self):
        """Keep the legacy ``date`` field in sync with ``date_time`` so reports
        based on either field stay consistent."""
        for record in self:
            if record.date_time:
                record.date = fields.Date.to_date(record.date_time)
            elif not record.date:
                record.date = fields.Date.context_today(record)

    def _prev_log_domain(self):
        """Domain used to fetch the previous fuel log for a vehicle.

        We deliberately exclude cancelled records (they are not real fills) and
        compare on ``date_time`` so that multiple fills on the same day order
        correctly.
        """
        self.ensure_one()
        return [
            ("vehicle_id", "=", self.vehicle_id.id),
            ("state", "!=", "cancelled"),
            ("id", "!=", self.id or self._origin.id or 0),
            ("date_time", "<=", self.date_time or fields.Datetime.now()),
        ]

    @api.depends("vehicle_id", "date_time", "state")
    def _compute_prev_log_stats(self):
        for record in self:
            prev_log = self.search(
                record._prev_log_domain(),
                limit=1,
                order="date_time desc, id desc",
            )
            record.prev_odometer = prev_log.odometer if prev_log else 0.0
            record.prev_date = prev_log.date if prev_log else False
            record.has_prev_log = bool(prev_log)

    @api.depends("odometer", "prev_odometer", "liter", "has_prev_log")
    def _compute_consumption(self):
        for record in self:
            # The very first fuel log for a vehicle has no real previous
            # odometer reading. Treating ``prev_odometer`` as 0 would attribute
            # the whole odometer reading to a single tank, making consumption
            # meaningless. Skip until at least one prior log exists.
            if not record.has_prev_log:
                record.distance = 0.0
                record.consumption_rate = 0.0
                continue
            distance = record.odometer - record.prev_odometer
            record.distance = distance if distance > 0 else 0.0
            if distance > 0:
                record.consumption_rate = record.liter / distance
            else:
                record.consumption_rate = 0.0

    @api.depends("vehicle_id", "liter", "distance", "state")
    def _compute_avg_consumption(self):
        """Lifetime average consumption rate per vehicle.

        Aggregated with a single ``_read_group`` to avoid the previous O(N x M)
        ``search`` per record, so the value can be safely used as a measure in
        graph / pivot views.
        """
        vehicle_ids = self.mapped("vehicle_id").ids
        averages = {}
        if vehicle_ids:
            # Exclude the first fill of each vehicle (distance == 0) so the
            # lifetime ratio is not skewed by litres without a measured
            # distance baseline.
            data = self.env["fleet.vehicle.log.fuel"]._read_group(
                [
                    ("vehicle_id", "in", vehicle_ids),
                    ("state", "!=", "cancelled"),
                    ("distance", ">", 0),
                ],
                groupby=["vehicle_id"],
                aggregates=["liter:sum", "distance:sum"],
            )
            for vehicle, total_liter, total_distance in data:
                averages[vehicle.id] = (
                    (total_liter / total_distance) if total_distance > 0 else 0.0
                )
        for record in self:
            record.avg_consumption_rate = averages.get(record.vehicle_id.id, 0.0)


    def _affected_neighbor_logs(self):
        """Return the fuel logs whose prev/avg stats may be invalidated by
        creating, updating or removing the records in ``self``.

        For each affected (vehicle, date_time) we recompute the *next* log so
        its ``prev_odometer`` / ``consumption_rate`` reflects the change.
        """
        Log = self.env["fleet.vehicle.log.fuel"]
        neighbors = Log.browse()
        for record in self:
            if not record.vehicle_id:
                continue
            next_log = Log.search(
                [
                    ("vehicle_id", "=", record.vehicle_id.id),
                    ("state", "!=", "cancelled"),
                    ("id", "!=", record.id),
                    ("date_time", ">=", record.date_time or fields.Datetime.now()),
                ],
                limit=1,
                order="date_time asc, id asc",
            )
            neighbors |= next_log
            neighbors |= Log.search(
                [
                    ("vehicle_id", "=", record.vehicle_id.id),
                    ("state", "!=", "cancelled"),
                ]
            )
        return neighbors

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        neighbors = records._affected_neighbor_logs() - records
        if neighbors:
            neighbors._compute_prev_log_stats()
            neighbors._compute_consumption()
            neighbors._compute_avg_consumption()
        return records

    def write(self, vals):
        trigger_fields = {"vehicle_id", "date_time", "odometer", "liter", "state"}
        affected_before = (
            self._affected_neighbor_logs()
            if trigger_fields.intersection(vals)
            else self.browse()
        )
        res = super().write(vals)
        if trigger_fields.intersection(vals):
            neighbors = (affected_before | self._affected_neighbor_logs()) - self
            if neighbors:
                neighbors._compute_prev_log_stats()
                neighbors._compute_consumption()
                neighbors._compute_avg_consumption()
        return res

    def unlink(self):
        neighbors = self._affected_neighbor_logs() - self
        res = super().unlink()
        if neighbors.exists():
            neighbors._compute_prev_log_stats()
            neighbors._compute_consumption()
            neighbors._compute_avg_consumption()
        return res

    @api.onchange("product_id")
    def _onchange_product_id(self):
        if self.product_id:
            self.price_per_liter = self.product_id.standard_price
            if self.product_id.is_fuel and self.product_id.fuel_location_id:
                self.location_id = self.product_id.fuel_location_id

    @api.onchange("liter", "price_per_liter", "amount")
    def _onchange_liter_price_amount(self):
        liter = float(self.liter)
        price_per_liter = float(self.price_per_liter)
        amount = float(self.amount)
        if (
            liter > 0
            and price_per_liter > 0
            and round(liter * price_per_liter, 2) != amount
        ):
            self.amount = round(liter * price_per_liter, 2)
        elif amount > 0 and liter > 0 and round(amount / liter, 2) != price_per_liter:
            self.price_per_liter = round(amount / liter, 2)
        elif (
            amount > 0
            and price_per_liter > 0
            and round(amount / price_per_liter, 2) != liter
        ):
            self.liter = round(amount / price_per_liter, 2)

    @api.depends("odometer_id", "odometer_id.value")
    def _compute_odometer(self):
        for record in self.filtered("odometer_id"):
            record.odometer = record.odometer_id.value

    def _inverse_odometer(self):
        if any(not x.odometer for x in self):
            raise UserError(
                _("Emptying the odometer value of a vehicle is not allowed.")
            )
        for record in self:
            self.odometer_id = self.env["fleet.vehicle.odometer"].create(
                record._prepare_fleet_vehicle_odometer_vals()
            )

    @api.depends("vehicle_id")
    def _compute_purchaser_id(self):
        for service in self:
            service.purchaser_id = service.vehicle_id.driver_id

    def button_running(self):
        self.filtered(lambda x: x.state == "todo").state = "running"
        return True

    def _prepare_fleet_vehicle_odometer_vals(self):
        return {
            "value": self.odometer,
            "date": self.date or fields.Date.context_today(self),
            "vehicle_id": self.vehicle_id.id,
        }

    def _prepare_fleet_vehicle_log_services_vals(self):
        return {
            "service_type_id": self.service_type_id.id,
            "description": self.description,
            "vehicle_id": self.vehicle_id.id,
            "amount": self.amount,
            "odometer": self.odometer,
            "vendor_id": self.vendor_id.id if self.vendor_id else False,
            "state": "done",
        }

    def button_todo(self):
        records = self.filtered(lambda x: x.state == "cancelled")
        records.state = "todo"
        return True

    def button_done(self):
        for item in self.filtered(lambda x: x.state == "running"):
            if item.product_id and item.location_id and item.liter > 0:
                move_vals = {
                    "product_id": item.product_id.id,
                    "product_uom_qty": item.liter,
                    "product_uom": item.product_id.uom_id.id,
                    "location_id": item.location_id.id,
                    "location_dest_id": item.location_dest_id.id
                    or self.env.ref("stock.stock_location_customers").id,
                    "origin": item.vehicle_id.name,
                }
                move = self.env["stock.move"].create(move_vals)
                move._action_confirm()
                move._action_assign()
                for line in move.move_line_ids:
                    line.quantity = line.quantity_product_uom
                move._action_done()
                item.stock_move_id = move.id

            item.service_id = self.env["fleet.vehicle.log.services"].create(
                self._prepare_fleet_vehicle_log_services_vals()
            )
            item.state = "done"
        return True

    def button_cancel(self):
        records = self.filtered(lambda x: x.state in ["todo", "running", "done"])
        records.mapped("service_id").sudo().unlink()
        records.state = "cancelled"
        # Cancel stock move TODO: Unreserve or Cancel?
        # For simplicity, we just leave it for now or user cancels manually.
        return True

    def action_view_stock_move(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "stock.move",
            "res_id": self.stock_move_id.id,
            "view_mode": "form",
            "target": "current",
        }
