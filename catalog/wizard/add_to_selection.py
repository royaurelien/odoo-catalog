from odoo import fields, models


class AddToSelection(models.TransientModel):
    _name = "add.to.selection"
    _description = "Add to selection Wizard"

    selection_id = fields.Many2one(comodel_name="catalog.selection")
    catalog_module_ids = fields.Many2many("catalog.module")

    def validate(self):
        """
        Add selected custom addons to current selection
        """
        self.selection_id.write(
            {"catalog_module_ids": [(4, rec.id) for rec in self.catalog_module_ids]}
        )
        return True
