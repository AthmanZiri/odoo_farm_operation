from odoo.tests.common import TransactionCase

class TestAccumulation(TransactionCase):

    def setUp(self):
        super(TestAccumulation, self).setUp()
        self.Template = self.env['worksheet.template']
        self.View = self.env['ir.ui.view']
        self.Fields = self.env['ir.model.fields']

    def test_accumulation_johndeere(self):
        """ Test that JD 8230 - 4500H template includes fields from 1500H, 500H, 250H """
        
        # Identify the 4500H template
        template = self.env.ref('maintenance_worksheet_templates.template_jd8230_4500h')
        self.assertTrue(template, "JD 8230 4500H template not found")
        
        # Check the View associated with it
        # Based on my logic, the view XML ID should be 'maintenance_worksheet_templates.view_jd8230_4500h'
        view = self.env.ref('maintenance_worksheet_templates.view_jd8230_4500h')
        self.assertTrue(view, "Generated View for 4500H not found")
        
        # Check if fields from lower intervals exist in the View Arch
        arch = view.arch
        
        # 250H Field: x_clean_fuel_tank_sump
        self.assertIn('x_clean_fuel_tank_sump', arch, "250H field missing from 4500H view")
        
        # 500H Field: x_change_engine_oil
        self.assertIn('x_change_engine_oil', arch, "500H field missing from 4500H view")
        
        # 4500H specific field: x_change_crank_damper
        self.assertIn('x_change_crank_damper', arch, "Specific 4500H field missing from view")
        
        # Check Groups exist
        self.assertIn('string="CLEAN"', arch)
        self.assertIn('string="CHANGE"', arch)

    def test_accumulation_bateman(self):
        """ Test that Bateman RB15 - 500H includes 250H fields """
        template = self.env.ref('maintenance_worksheet_templates.template_bateman_rb15_500h')
        view = self.env.ref('maintenance_worksheet_templates.view_bateman_rb15_500h')
        
        arch = view.arch
        
        # 250H Field: x_inspect_air_intake_rb15
        self.assertIn('x_inspect_air_intake_rb15', arch, "250H field missing from 500H view")
        
        # 500H Field
        self.assertIn('x_change_engine_oil_rb15', arch, "500H field missing from 500H view")

