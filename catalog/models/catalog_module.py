import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CatalogTemplate(models.Model):
    _name = "catalog.module"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Catalog Template"
    _order = "name, id"

    def _get_default_favorite_user_ids(self):
        return [(6, 0, [self.env.uid])]

    name = fields.Char(
        index="trigram",
        required=True,
    )
    technical_name = fields.Char(
        index="trigram",
        required=True,
    )
    active = fields.Boolean(
        default=True,
        help="If unchecked, it will allow you to hide the entry without removing it.",
    )

    entry_ids = fields.One2many(
        comodel_name="catalog.entry",
        inverse_name="catalog_module_id",
        string="Entries",
        required=True,
    )
    # performance: product_variant_id provides prefetching on the first product variant only
    entry_id = fields.Many2one(
        comodel_name="catalog.entry",
        string="Entry",
        compute="_compute_entry_id",
    )
    entry_count = fields.Integer(
        string="# Entries",
        compute="_compute_entry_count",
    )
    is_entry = fields.Boolean(
        compute="_compute_is_entry",
    )

    path = fields.Char(
        compute="_compute_path",
        # inverse="_set_path",
        store=True,
    )

    web_description = fields.Text(
        compute="_compute_web_description",
        inverse="_set_web_description",
        store=True,
    )

    version_ids = fields.Many2many(
        comodel_name="catalog.version",
        string="Versions",
        compute="_compute_versions",
        compute_sudo=True,
        store=True,
    )
    icon_image = fields.Binary(
        string="Icon",
        compute="_compute_icon",
        # related="entry_id.icon_image",
    )
    favorite_user_ids = fields.Many2many(
        "res.users",
        "module_favorite_user_rel",
        "catalog_module_id",
        "user_id",
        default=_get_default_favorite_user_ids,
        string="Favorites",
    )
    is_favorite = fields.Boolean(
        compute="_compute_is_favorite",
        inverse="_inverse_is_favorite",
        search="_search_is_favorite",
        compute_sudo=True,
        string="Show Module on Dashboard",
    )
    _sql_constraints = [
        (
            "technical_name_uniq",
            "unique (technical_name)",
            "Technical name already exists !",
        ),
    ]

    @api.depends("entry_ids", "entry_ids.version_id")
    def _compute_versions(self):
        for record in self:
            if not record.entry_ids:
                record.version_ids = False
                continue

            ids = list(set(record.entry_ids.version_id.ids))
            record.version_ids = [fields.Command.set(ids)]

    @api.depends("entry_ids")
    def _compute_entry_id(self):
        for p in self:
            p.entry_id = p.entry_ids[:1].id

    @api.depends("entry_ids.catalog_module_id")
    def _compute_entry_count(self):
        for module in self:
            module.entry_count = len(module.entry_ids)

    def _compute_is_entry(self):
        self.is_entry = False

    @api.depends("entry_ids.icon_image")
    def _compute_icon(self):
        self._compute_template_field_from_variant_field("icon_image")

    @api.depends("entry_ids.path")
    def _compute_path(self):
        self._compute_template_field_from_variant_field("path")

    def _set_path(self):
        self._set_entry_variant_field("path")

    @api.depends("entry_ids.web_description")
    def _compute_web_description(self):
        self._compute_template_field_from_variant_field("web_description")

    def _set_web_description(self):
        self._set_entry_variant_field("web_description")

    def _compute_template_field_from_variant_field(self, fname, default=False):
        """Sets the value of the given field based on the module variant values

        Equals to entry_ids[fname] if it's a single variant product.
        Otherwise, sets the value specified in ``default``.
        It's used to compute fields like barcode, weight, volume..

        :param str fname: name of the field to compute
            (field name must be identical between product.product & product.module models)
        :param default: default value to set when there are multiple or no variants on the module
        :return: None
        """
        for module in self:
            variant_count = len(module.entry_ids)
            if variant_count == 1:
                module[fname] = module.entry_ids[fname]
            elif variant_count == 0 and self.env.context.get("active_test", True):
                # If the product has no active variants, retry without the active_test
                template_ctx = module.with_context(active_test=False)
                template_ctx._compute_template_field_from_variant_field(
                    fname, default=default
                )
            else:
                module[fname] = default

    def _set_entry_variant_field(self, fname):
        """Propagate the value of the given field from the templates to their unique variant.

        Only if it's a single variant product.
        It's used to set fields like barcode, weight, volume..

        :param str fname: name of the field whose value should be propagated to the variant.
            (field name must be identical between product.product & product.module models)
        """
        for module in self:
            count = len(module.entry_ids)
            if count == 1:
                module.entry_ids[fname] = module[fname]
            elif count == 0:
                archived_variants = self.with_context(active_test=False).entry_ids
                if len(archived_variants) == 1:
                    archived_variants[fname] = module[fname]

    @api.model
    def _search_is_favorite(self, operator, value):
        if operator not in ["=", "!="] or not isinstance(value, bool):
            raise NotImplementedError(_("Operation not supported"))
        return [
            (
                "favorite_user_ids",
                "in" if (operator == "=") == value else "not in",
                self.env.uid,
            )
        ]

    def _compute_is_favorite(self):
        for record in self:
            record.is_favorite = self.env.user in record.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_records = not_fav_records = self.env["catalog.module"].sudo()
        for record in self:
            if self.env.user in record.favorite_user_ids:
                favorite_records |= record
            else:
                not_fav_records |= record

        # Project User has no write access for record.
        not_fav_records.write({"favorite_user_ids": [(4, self.env.uid)]})
        favorite_records.write({"favorite_user_ids": [(3, self.env.uid)]})

    def _get_default_favorite_user_ids(self):
        return [(6, 0, [self.env.uid])]

    def _prepare_variant_values(self, combination=None):
        self.ensure_one()
        return {
            "catalog_module_id": self.id,
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
            # ).entry_ids.sorted(lambda p: (p.active, -p.id))

            variants_to_create.append(tmpl_id._prepare_variant_values())

        if variants_to_activate:
            variants_to_activate.write({"active": True})
        if variants_to_create:
            Entry.create(variants_to_create)
        if variants_to_unlink:
            variants_to_unlink._unlink_or_archive()
            # prevent change if exclusion deleted module by deleting last variant
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

    def _get_related_fields_variant_template(self):
        """Return a list of fields present on module and variants models and that are related"""
        return ["path", "web_description", "icon_image"]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._sanitize_vals(vals)
        templates = super().create(vals_list)
        if self._context.get("create_catalog_entry", True):
            templates._create_variant_ids()

        # This is needed to set given values to first variant after creation
        for module, vals in zip(templates, vals_list):
            related_vals = {}
            for field_name in self._get_related_fields_variant_template():
                if vals.get(field_name):
                    related_vals[field_name] = vals[field_name]
            if related_vals:
                module.write(related_vals)

        return templates

    def write(self, vals):
        self._sanitize_vals(vals)

        res = super().write(vals)
        if self._context.get("create_catalog_entry", False) or (
            vals.get("active") and len(self.entry_ids) == 0
        ):
            self._create_variant_ids()
        if "active" in vals and not vals.get("active"):
            self.with_context(active_test=False).mapped("entry_ids").write(
                {"active": vals.get("active")}
            )
        return res

    def action_view_branches(self):
        self.ensure_one()

        return {}

    def action_view_repositories(self):
        self.ensure_one()

        return {}

    def action_view_entries(self):  # pylint: disable=C0116
        action = self.env.ref("catalog.action_view_entries").read()[0]
        action["domain"] = [("id", "in", self.entry_ids.ids)]

        return action
