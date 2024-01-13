import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogEntry(models.Model):
    _name = "catalog.entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"catalog.template": "catalog_tmpl_id"}
    _description = "Catalog Entry"

    active = fields.Boolean(
        "Active",
        default=True,
        help="If unchecked, it will allow you to hide the entry without removing it.",
    )
    catalog_tmpl_id = fields.Many2one(
        "Catalog.template",
        "Catalog Template",
        auto_join=True,
        index=True,
        ondelete="cascade",
        required=True,
    )
    is_entry_variant = fields.Boolean(
        compute="_compute_is_entry_variant",
    )

    branch = fields.Char(
        index=True,
    )
    # description = fields.Text()
    # web_description = fields.Html()
    # summary = fields.Char()
    # technical_name = fields.Char(required=True, index=True)
    # application = fields.Boolean(default=False)
    # depends = fields.Char()
    # active = fields.Boolean(default=True)
    # icon = fields.Char("Icon URL")
    # icon_image = fields.Binary(string="Icon")
    # url = fields.Char()

    # author = fields.Char()

    def _compute_is_entry_variant(self):
        self.is_entry_variant = True
