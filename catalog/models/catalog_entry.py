import json
import logging

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
        "catalog.template",
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

    manifest = fields.Text()

    version = fields.Char(
        compute="_compute_manifest",
        store=True,
    )
    license = fields.Char(
        compute="_compute_manifest",
        store=True,
    )
    author = fields.Char(
        compute="_compute_manifest",
        store=True,
    )
    website = fields.Char(
        compute="_compute_manifest",
        store=True,
    )
    category = fields.Char(
        compute="_compute_manifest",
        store=True,
    )

    path = fields.Char(
        index=True,
        required=True,
    )
    checksum = fields.Char(
        index=True,
        required=True,
    )
    # description = fields.Text()
    # web_description = fields.Html()
    # summary = fields.Char()
    # technical_name = fields.Char(required=True, index=True)
    # application = fields.Boolean(default=False)
    # depends = fields.Char()
    # icon = fields.Char("Icon URL")
    # icon_image = fields.Binary(string="Icon")
    # url = fields.Char()

    # author = fields.Char()

    def _get_manifest_fields(self):
        return ["version", "license", "author", "website", "category"]

    def _get_manifest_values(self):
        self.ensure_one()
        manifest = {}
        fields = self._get_manifest_fields()

        if self.manifest:
            try:
                vals = json.loads(self.manifest)
                manifest = vals.get("manifest", {})
            except Exception:
                pass
        return {field: manifest.get(field, "") for field in fields}

    @api.depends("manifest")
    def _compute_manifest(self):
        for record in self:
            vals = record._get_manifest_values()
            record.write(vals)

    def _compute_is_entry_variant(self):
        self.is_entry_variant = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.catalog_tmpl_id._sanitize_vals(vals)
        products = super(
            CatalogEntry, self.with_context(create_catalog_entry=False)
        ).create(vals_list)
        # `_get_variant_id_for_combination` depends on existing variants
        self.env.registry.clear_cache()
        return products

    def write(self, values):
        self.catalog_tmpl_id._sanitize_vals(values)
        res = super().write(values)
        if "product_template_attribute_value_ids" in values:
            # `_get_variant_id_for_combination` depends on `product_template_attribute_value_ids`
            self.env.registry.clear_cache()
        elif "active" in values:
            # `_get_first_possible_variant_id` depends on variants active state
            self.env.registry.clear_cache()
        return res
