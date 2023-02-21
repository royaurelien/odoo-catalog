# -*- coding: utf-8 -*-

from odoo import fields, models


class AddonsSelectionWizard(models.TransientModel):
    _name = "addons.selection.wizard"
    _description = "Addons Selection Wizard"

    selection_id = fields.Many2one(comodel_name="custom.addon.selection")
    custom_addon_ids = fields.Many2many("custom.addon")

    def validate(self):
        """
        Add selected custom addons to current selection
        """
        self.selection_id.write(
            {"custom_addon_ids": [(4, rec.id) for rec in self.custom_addon_ids]}
        )
        return True
