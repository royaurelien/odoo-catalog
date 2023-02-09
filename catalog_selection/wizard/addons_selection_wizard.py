# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_compare


class AddonsSelectionWizard(models.TransientModel):
    _name = "addons.selection.wizard"
    _description = "Addons Selection Wizard"

    selection_id = fields.Many2one(comodel_name="custom.addon.selection")
    custom_addon_ids = fields.Many2many("custom.addon")

    def validate(self):
        # list(map(lambda x: (4, x), self.custom_addon_ids.ids))
        self.selection_id.write(
            {"custom_addon_ids": [(4, rec.id) for rec in self.custom_addon_ids]}
        )
        return True
