from odoo import models


class CustomAddon(models.Model):
    _inherit = "custom.addon"

    def action_add_to_selection(self):
        """
        Add custom addons to selection
        """
        return self.env["custom.addon.selection"]._add_to_selection(self.ids)
