import logging

from odoo import _, api, fields, models

_logger = logging.getLogger(__name__)


class CatalogSelection(models.Model):
    _name = "catalog.selection"
    _description = "Catalog Selection"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    user_id = fields.Many2one(
        "res.users",
        string="Responsible",
        required=True,
        default=lambda self: self.env.user,
    )
    # tag_ids = fields.Many2many("custom.addon.tags", string="Tags")

    catalog_module_ids = fields.Many2many(
        string="Modules",
        comodel_name="catalog.module",
        relation="catalog_module_selection_rel",
        column1="selection_id",
        column2="catalog_module_id",
        tracking=True,
    )

    catalog_module_count = fields.Integer(
        compute="_compute_modules",
        string="# Modules",
        store=True,
    )
    note = fields.Html()

    @api.depends("catalog_module_ids")
    def _compute_modules(self):
        for record in self:
            record.catalog_module_count = len(record.catalog_module_ids)

    def action_view_modules(self):
        action = self.env.ref("catalog.action_view_modules").read()[0]
        action["domain"] = [("id", "in", self.catalog_module_ids.ids)]

        return action

    @api.model
    def _add_to_selection(self, ids):
        view_id = self.env.ref("catalog.add_to_selection_view_form").id
        vals = {
            "catalog_module_ids": [(6, 0, ids)],
        }

        wizard = self.env["add.to.selection"].create(vals)

        return {
            "name": _("Add to selection"),
            "view_mode": "form",
            "res_model": "add.to.selection",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "target": "new",
        }
