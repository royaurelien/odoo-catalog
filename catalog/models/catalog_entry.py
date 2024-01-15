import base64
import itertools
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogEntry(models.Model):
    _name = "catalog.entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"catalog.template": "catalog_tmpl_id"}
    _description = "Catalog Entry"
    _order = "name, id"

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
    data = fields.Text()
    version = fields.Char()
    version_id = fields.Many2one(
        comodel_name="catalog.version",
        string="Major Version",
    )

    license = fields.Char()
    website = fields.Char()
    category = fields.Char()
    summary = fields.Char()
    description = fields.Char()
    depends = fields.Char()
    repository = fields.Char()
    organization = fields.Char()

    has_data = fields.Boolean()
    has_views = fields.Boolean()
    has_security = fields.Boolean()

    path = fields.Char(
        index=True,
        required=True,
    )
    uuid = fields.Char(
        index=True,
        required=True,
    )

    author_ids = fields.Many2many(
        comodel_name="catalog.author",
        string="Authors",
    )
    repository_id = fields.Many2one(
        comodel_name="catalog.repository",
    )
    branch_id = fields.Many2one(
        comodel_name="catalog.branch",
    )
    category_id = fields.Many2one(
        comodel_name="catalog.category",
    )
    icon = fields.Char(
        string="Icon URL",
    )
    icon_image = fields.Binary(
        string="Icon",
    )
    web_description = fields.Html()

    # application = fields.Boolean(default=False)
    # depends = fields.Char()

    # url = fields.Char()

    # author = fields.Char()

    _sql_constraints = [
        (
            "uuid_uniq",
            "unique (uuid)",
            "UUID already exists !",
        ),
    ]

    # def _get_manifest_fields(self):
    #     return ["version", "license", "author", "website", "category"]

    # def _get_manifest_values(self):
    #     self.ensure_one()
    #     manifest = {}
    #     fields = self._get_manifest_fields()

    #     if self.manifest:
    #         try:
    #             vals = json.loads(self.manifest)
    #             manifest = vals.get("manifest", {})
    #         except Exception:
    #             pass
    #     return {field: manifest.get(field, "") for field in fields}

    # @api.depends("manifest")
    # def _compute_manifest(self):
    #     for record in self:
    #         vals = record._get_manifest_values()
    #         record.write(vals)

    def _compute_is_entry_variant(self):
        self.is_entry_variant = True

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self.catalog_tmpl_id._sanitize_vals(vals)
        entries = super(
            CatalogEntry, self.with_context(create_catalog_entry=False)
        ).create(vals_list)
        # `_get_variant_id_for_combination` depends on existing variants
        self.env.registry.clear_cache()
        return entries

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

    def _ext_prepare_vals_list(self, vals_list):
        # Search or create all authors
        names = list(set(itertools.chain(*[vals["authors"] for vals in vals_list])))
        authors = self.env["catalog.author"].search_or_create(names)

        # Search or create all repositories
        paths = [vals["repository"] for vals in vals_list]
        repositories = self.env["catalog.repository"].search_or_create(paths)

        # Search or create all repositories
        paths = [vals["branch"] for vals in vals_list]
        branches = self.env["catalog.branch"].search_or_create(paths)
        branches.merge_with_repositories(repositories)

        # Search or create all needed versions
        names = [vals["major_version"] for vals in vals_list]
        versions = self.env["catalog.version"].search_or_create(names)

        # Search or create all needed versions
        names = [vals["category"] for vals in vals_list]
        categories = self.env["catalog.category"].search_or_create(names)

        exclude = ["authors", "major_version", "index", "icon"]
        new_vals_list = []

        for vals in vals_list:
            if "data" in vals:
                vals["data"] = ", ".join(vals.get("data", []))

            if "depends" in vals:
                vals["depends"] = ", ".join(vals.get("depends", []))

            if vals.get("authors"):
                current_authors = authors.filtered_domain(
                    [("name", "in", vals["authors"])]
                )
                if current_authors:
                    vals["author_ids"] = [fields.Command.set(current_authors.ids)]

            if vals.get("repository"):
                res = repositories.filtered_domain([("path", "=", vals["repository"])])
                vals["repository_id"] = res.id if res else False

            if vals.get("branch"):
                res = branches.filtered_domain([("path", "=", vals["branch"])])
                vals["branch_id"] = res.id if res else False

            if vals.get("major_version"):
                res = versions.filtered_domain([("name", "=", vals["major_version"])])
                vals["version_id"] = res.id if res else False

            if vals.get("category"):
                res = categories.filtered_domain([("name", "=", vals["category"])])
                vals["category_id"] = res.id if res else False

            if vals.get("index"):
                vals["web_description"] = base64.b64decode(vals.get("index"))

            if vals.get("icon"):
                vals["icon_image"] = vals.get("icon")

            vals = {k: v for k, v in vals.items() if k not in exclude}
            new_vals_list.append(vals)

        return new_vals_list

    @api.model_create_multi
    def update_or_create(self, vals_list):
        for vals in vals_list:
            self.catalog_tmpl_id._sanitize_vals(vals)

        entries = self
        vals_list = self._ext_prepare_vals_list(vals_list)

        vals_by_uuid = {vals["uuid"]: vals for vals in vals_list}
        all_uuid = set(vals_by_uuid.keys())
        data = self.search_read(
            [("uuid", "in", list(all_uuid))], ["id", "uuid"], load=""
        )

        _logger.error(data)

        # dict([(item[0], item[1]) for item in data])
        # dict([(item[1], item[0]) for item in data])

        to_update = {item["uuid"]: item["id"] for item in data}
        to_update_inverse = {str(item["id"]): item["uuid"] for item in data}

        uuid_to_create = all_uuid - set(to_update.keys())
        to_create = {
            vals["technical_name"]: vals
            for uuid, vals in vals_by_uuid.items()
            if uuid in uuid_to_create
        }

        if to_update:
            records = self.browse(to_update.values())
            for record in records:
                uuid = to_update_inverse.get(str(record.id))
                record.write(vals_by_uuid.get(uuid))
                entries |= record

        if to_create:
            data = self.search_read(
                [("technical_name", "in", list(to_create.keys()))],
                ["technical_name", "catalog_tmpl_id"],
                load="",
            )
            data = {item["technical_name"]: item["catalog_tmpl_id"] for item in data}

            for name in to_create.keys():
                catalog_tmpl_id = data.get(name)
                if catalog_tmpl_id:
                    to_create[name].update({"catalog_tmpl_id": catalog_tmpl_id})

            entries |= self.create(to_create.values())

        return entries
