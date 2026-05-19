# Copyright 2024 Tecnativa - Víctor Martínez
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl
from odoo.exceptions import UserError
from odoo.tests import Form
from odoo.tools import mute_logger

from .common import TestFleetVehicleLogFuelBase


class TestFleetVehicleLogFuelMisc(TestFleetVehicleLogFuelBase):
    @mute_logger("odoo.models.unlink")
    def test_fleet_vehicle_log_fuel_process(self):
        fuel_form = Form(
            self.env["fleet.vehicle.log.fuel"].with_context(
                default_vehicle_id=self.vehicle.id
            )
        )
        with self.assertRaises(UserError):
            fuel_form.odometer = 0
            fuel_form.save()
        fuel_form.odometer = 5000
        fuel = fuel_form.save()
        self.assertTrue(fuel.odometer_id)
        self.assertEqual(self.vehicle.odometer, 5000)
        self.assertEqual(self.vehicle.fuel_count, 1)
        res = self.vehicle.action_view_log_fuel()
        items = self.env[res["res_model"]].search(res["domain"])
        self.assertIn(fuel, items)
        fuel.button_running()
        self.assertEqual(fuel.state, "running")
        fuel.button_done()
        self.assertEqual(fuel.state, "done")
        self.assertTrue(fuel.service_id)
        self.assertEqual(fuel.service_id.service_type_id, fuel.service_type_id)
        self.assertEqual(fuel.service_id.state, "done")
        fuel.button_cancel()
        self.assertEqual(fuel.state, "cancelled")
        self.assertFalse(fuel.service_id)
        fuel.button_todo()
        self.assertEqual(fuel.state, "todo")

    def test_fleet_vehicle_log_fuel_onchange(self):
        # Check amount
        fuel_form_1 = Form(
            self.env["fleet.vehicle.log.fuel"].with_context(
                default_vehicle_id=self.vehicle.id
            )
        )
        fuel_form_1.liter = 50
        fuel_form_1.price_per_liter = 1.5
        self.assertEqual(fuel_form_1.amount, 75)
        # Check price_per_liter
        fuel_form_2 = Form(
            self.env["fleet.vehicle.log.fuel"].with_context(
                default_vehicle_id=self.vehicle.id
            )
        )
        fuel_form_2.amount = 75
        fuel_form_2.liter = 50
        self.assertEqual(fuel_form_2.price_per_liter, 1.5)
        # Check liter
        fuel_form_2 = Form(
            self.env["fleet.vehicle.log.fuel"].with_context(
                default_vehicle_id=self.vehicle.id
            )
        )
        fuel_form_2.amount = 75
        fuel_form_2.price_per_liter = 1.5
        self.assertEqual(fuel_form_2.liter, 50)


class TestFleetVehicleLogFuelReport(TestFleetVehicleLogFuelBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Create log fuel + log service to check report after
        fuel = cls.env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": cls.vehicle.id,
                "date": "2024-01-01",
                "amount": 75,
                "price_per_liter": 1.5,
                "liter": 50,
            }
        )
        fuel.button_running()
        fuel.button_done()

    def test_fleet_vehicle_cost_report(self):
        items = self.env["fleet.vehicle.cost.report"].search(
            [("vehicle_id", "=", self.vehicle.id), ("date_start", "=", "2024-01-01")]
        )
        self.assertIn("fuel", items.mapped("cost_type"))
        self.assertEqual(
            sum(items.filtered(lambda x: x.cost_type == "fuel").mapped("cost")), 75
        )


class TestFleetVehicleLogFuelUtilization(TestFleetVehicleLogFuelBase):
    """Cover the utilization stats used by the fuel reporting graph/pivot."""

    def _create_log(self, date_time, odometer, liter, state="done"):
        log = self.env["fleet.vehicle.log.fuel"].create(
            {
                "vehicle_id": self.vehicle.id,
                "date_time": date_time,
                "odometer": odometer,
                "liter": liter,
                "amount": liter * 1.5,
                "price_per_liter": 1.5,
            }
        )
        if state == "done":
            log.button_running()
            log.button_done()
        elif state == "cancelled":
            log.button_cancel()
        return log

    def test_first_fill_has_no_consumption(self):
        log = self._create_log("2024-01-01 08:00:00", 1000, 50)
        self.assertFalse(log.has_prev_log)
        self.assertEqual(log.distance, 0.0)
        self.assertEqual(log.consumption_rate, 0.0)

    def test_second_fill_consumption_rate(self):
        self._create_log("2024-01-01 08:00:00", 1000, 50)
        second = self._create_log("2024-01-15 08:00:00", 1100, 25)
        self.assertTrue(second.has_prev_log)
        self.assertEqual(second.distance, 100.0)
        self.assertAlmostEqual(second.consumption_rate, 0.25)

    def test_backdated_log_recomputes_neighbor(self):
        first = self._create_log("2024-02-01 08:00:00", 1100, 25)
        # Initially first is the only log -> no consumption stats
        self.assertEqual(first.distance, 0.0)
        # Insert an earlier log; the originally-first record should now have a
        # valid previous odometer and consumption rate.
        self._create_log("2024-01-01 08:00:00", 1000, 50)
        first.invalidate_recordset()
        self.assertTrue(first.has_prev_log)
        self.assertEqual(first.distance, 100.0)
        self.assertAlmostEqual(first.consumption_rate, 0.25)

    def test_cancelled_log_is_ignored_for_prev(self):
        self._create_log("2024-01-01 08:00:00", 1000, 50)
        self._create_log("2024-01-10 08:00:00", 1050, 30, state="cancelled")
        third = self._create_log("2024-01-20 08:00:00", 1100, 20)
        # The cancelled log between the two real fills must NOT be the prev log
        self.assertEqual(third.prev_odometer, 1000)
        self.assertEqual(third.distance, 100.0)

    def test_avg_consumption_rate_is_aggregated(self):
        self._create_log("2024-01-01 08:00:00", 1000, 50)
        self._create_log("2024-01-15 08:00:00", 1100, 25)
        self._create_log("2024-02-01 08:00:00", 1200, 30)
        logs = self.env["fleet.vehicle.log.fuel"].search(
            [("vehicle_id", "=", self.vehicle.id)]
        )
        # Lifetime CR = total liter on non-first fills / total distance.
        # The first fill carries 0 distance so it does not contribute.
        avg = logs[0].avg_consumption_rate
        self.assertGreater(avg, 0.0)
        # All logs for the same vehicle expose the same lifetime average
        self.assertTrue(all(abs(log.avg_consumption_rate - avg) < 1e-9 for log in logs))

    def test_date_synced_from_date_time(self):
        log = self._create_log("2024-03-15 14:30:00", 1000, 50)
        self.assertEqual(str(log.date), "2024-03-15")

    def test_grouping_dimensions_populated(self):
        log = self._create_log("2024-01-01 08:00:00", 1000, 50)
        # Related fields used as grouping dimensions in the report views must
        # be readable on a stored fuel log even when their value is empty.
        self.assertEqual(log.model_id, self.vehicle.model_id)
        self.assertEqual(log.category_id, self.vehicle.category_id)
        self.assertEqual(log.fuel_type, self.vehicle.fuel_type)
