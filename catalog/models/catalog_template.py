import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogTemplate(models.Model):
    _name = "catalog.template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Catalog Template"

    name = fields.Char(
        "Name",
        index="trigram",
        required=True,
        translate=True,
    )
    active = fields.Boolean(
        "Active",
        default=True,
        help="If unchecked, it will allow you to hide the entry without removing it.",
    )

    entry_variant_ids = fields.One2many(
        "catalog.entry",
        "catalog_tmpl_id",
        "Entries",
        required=True,
    )
    # performance: product_variant_id provides prefetching on the first product variant only
    entry_variant_id = fields.Many2one(
        "catalog.entry",
        "Entry",
        compute="_compute_entry_variant_id",
    )
    entry_variant_count = fields.Integer(
        "# Entry Variants",
        compute="_compute_entry_variant_count",
    )
    is_entry_variant = fields.Boolean(
        compute="_compute_is_entry_variant",
    )

    branch = fields.Char(
        "Internal Reference",
        compute="_compute_branch",
        inverse="_set_branch",
        store=True,
    )

    @api.depends("entry_variant_ids")
    def _compute_entry_variant_id(self):
        for p in self:
            p.entry_variant_id = p.entry_variant_ids[:1].id

    @api.depends("entry_variant_ids.catalog_tmpl_id")
    def _compute_entry_variant_count(self):
        for template in self:
            template.entry_variant_count = len(template.entry_variant_ids)

    def _compute_is_entry_variant(self):
        self.is_entry_variant = False

    @api.depends("entry_variant_ids.branch")
    def _compute_branch(self):
        self._compute_template_field_from_variant_field("branch")

    def _set_branch(self):
        self._set_entry_variant_field("branch")

    def _compute_template_field_from_variant_field(self, fname, default=False):
        """Sets the value of the given field based on the template variant values

        Equals to entry_variant_ids[fname] if it's a single variant product.
        Otherwise, sets the value specified in ``default``.
        It's used to compute fields like barcode, weight, volume..

        :param str fname: name of the field to compute
            (field name must be identical between product.product & product.template models)
        :param default: default value to set when there are multiple or no variants on the template
        :return: None
        """
        for template in self:
            variant_count = len(template.entry_variant_ids)
            if variant_count == 1:
                template[fname] = template.entry_variant_ids[fname]
            elif variant_count == 0 and self.env.context.get("active_test", True):
                # If the product has no active variants, retry without the active_test
                template_ctx = template.with_context(active_test=False)
                template_ctx._compute_template_field_from_variant_field(
                    fname, default=default
                )
            else:
                template[fname] = default

    def _set_entry_variant_field(self, fname):
        """Propagate the value of the given field from the templates to their unique variant.

        Only if it's a single variant product.
        It's used to set fields like barcode, weight, volume..

        :param str fname: name of the field whose value should be propagated to the variant.
            (field name must be identical between product.product & product.template models)
        """
        for template in self:
            count = len(template.entry_variant_ids)
            if count == 1:
                template.entry_variant_ids[fname] = template[fname]
            elif count == 0:
                archived_variants = self.with_context(
                    active_test=False
                ).entry_variant_ids
                if len(archived_variants) == 1:
                    archived_variants[fname] = template[fname]
