import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CatalogTemplate(models.Model):
    _name = "catalog.template"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Catalog Template"

    name = fields.Char(
        index="trigram",
        required=True,
        translate=True,
    )
    technical_name = fields.Char(
        index="trigram",
        required=True,
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the entry without removing it.",
    )

    entry_variant_ids = fields.One2many(
        comodel_name="catalog.entry",
        inverse_name="catalog_tmpl_id",
        string="Entries",
        required=True,
    )
    # performance: product_variant_id provides prefetching on the first product variant only
    entry_variant_id = fields.Many2one(
        comodel_name="catalog.entry",
        string="Entry",
        compute="_compute_entry_variant_id",
    )
    entry_variant_count = fields.Integer(
        string="# Entry Variants",
        compute="_compute_entry_variant_count",
    )
    is_entry_variant = fields.Boolean(
        compute="_compute_is_entry_variant",
    )

    branch = fields.Char(
        compute="_compute_branch",
        inverse="_set_branch",
        store=True,
    )

    manifest = fields.Text(
        compute="_compute_manifest",
        inverse="_set_manifest",
        store=True,
    )

    _sql_constraints = [
        (
            "technical_name_uniq",
            "unique (technical_name)",
            "Technical name already exists !",
        ),
    ]

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

    @api.depends("entry_variant_ids.manifest")
    def _compute_manifest(self):
        self._compute_template_field_from_variant_field("manifest")

    def _set_manifest(self):
        self._set_entry_variant_field("manifest")

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

    def _prepare_variant_values(self, combination=None):
        self.ensure_one()
        return {
            "catalog_tmpl_id": self.id,
            # 'product_template_attribute_value_ids': [(6, 0, combination.ids)],
            "active": self.active,
        }

    def _create_variant_ids(self):
        if not self:
            return
        self.env.flush_all()
        Entry = self.env["catalog.entry"]

        variants_to_create = []
        variants_to_activate = Entry
        variants_to_unlink = Entry

        for tmpl_id in self:
            # all_variants = tmpl_id.with_context(
            #     active_test=False
            # ).entry_variant_ids.sorted(lambda p: (p.active, -p.id))

            variants_to_create.append(tmpl_id._prepare_variant_values())

        if variants_to_activate:
            variants_to_activate.write({"active": True})
        if variants_to_create:
            Entry.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()
            # prevent change if exclusion deleted template by deleting last variant
            if self.exists() != self:
                raise UserError(
                    _("Please archive or delete your product directly if intended.")
                )

    def _sanitize_vals(self, vals):
        """Sanitize vales for writing/creating product templates and variants.

        Values need to be sanitized to keep values synchronized, and to be able to preprocess the
        vals in extensions of create/write.
        :param vals: create/write values dictionary
        """
        if "type" in vals and "detailed_type" not in vals:
            if vals["type"] not in self.mapped("type"):
                vals["detailed_type"] = vals["type"]
        if "detailed_type" in vals and "type" not in vals:
            type_mapping = self._detailed_type_mapping()
            vals["type"] = type_mapping.get(
                vals["detailed_type"], vals["detailed_type"]
            )

    def _get_related_fields_variant_template(self):
        """Return a list of fields present on template and variants models and that are related"""
        return ["branch", "manifest"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_vals(vals)
        templates = super().create(vals_list)
        if self._context.get("create_catalog_entry", True):
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for template, vals in zip(templates, vals_list):
            related_vals = {}
            for field_name in self._get_related_fields_variant_template():
                if vals.get(field_name):
                    related_vals[field_name] = vals[field_name]
            if related_vals:
                template.write(related_vals)

        return templates

    def write(self, vals):
        self._sanitize_vals(vals)

        res = super().write(vals)
        if self._context.get("create_catalog_entry", True) or (
            vals.get("active") and len(self.entry_variant_ids) == 0
        ):
            self._create_variant_ids()
        if "active" in vals and not vals.get("active"):
            self.with_context(active_test=False).mapped("entry_variant_ids").write(
                {"active": vals.get("active")}
            )
        return res
