from odoo import fields, models


class IrModuleCategory(models.Model):
    _inherit = "ir.module.category"

    custom_addon_ids = fields.One2many(
        comodel_name="custom.addon", inverse_name="category_id"
    )
