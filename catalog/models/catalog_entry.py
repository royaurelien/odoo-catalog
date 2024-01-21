import base64
import itertools
import logging
from itertools import groupby
from operator import itemgetter

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogEntry(models.Model):
    _name = "catalog.entry"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _inherits = {"catalog.module": "catalog_module_id"}
    _description = "Catalog Entry"
    _order = "name, id"

    active = fields.Boolean(
        "Active",
        default=True,
        help="If unchecked, it will allow you to hide the entry without removing it.",
    )
    catalog_module_id = fields.Many2one(
        "catalog.module",
        "Catalog Template",
        auto_join=True,
        index=True,
        ondelete="cascade",
        required=True,
    )
    is_entry = fields.Boolean(
        compute="_compute_is_entry",
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

    branch_id = fields.Many2one(
        comodel_name="catalog.branch",
    )
    repository_id = fields.Many2one(
        related="branch_id.repository_id",
        store=True,
    )
    organization_id = fields.Many2one(
        related="branch_id.repository_id.organization_id",
        store=True,
    )
    category_id = fields.Many2one(
        comodel_name="catalog.category",
    )
    icon = fields.Char(
        string="Icon URL",
    )
    icon_image = fields.Image(
        string="Icon",
    )
    web_description = fields.Html()
    manifest_url = fields.Char()
    index_url = fields.Char()
    icon_url = fields.Char()
    module_url = fields.Char()

    depend_ids = fields.One2many(
        comodel_name="catalog.module",
        compute="_compute_depends",
        string="Depends",
    )
    depend_count = fields.Integer(
        compute="_compute_depends",
        string="# Depends",
    )
    depend_count_total = fields.Integer(
        compute="_compute_depends",
        string="# Depends (file)",
    )
    initialized = fields.Boolean(
        default=False,
    )

    _sql_constraints = [
        (
            "uuid_uniq",
            "unique (uuid)",
            "UUID already exists !",
        ),
    ]

    def _compute_is_entry(self):
        self.is_entry = True

    @api.depends("depends")
    def _compute_depends(self):
        Module = self.env["catalog.module"]  # pylint: disable=C0103
        for record in self:
            if not record.depends:
                record.depend_ids = False
                record.depend_count = 0
                record.depend_count_total = 0
                continue

            names = list(set(map(str.strip, record.depends.split(","))))
            depends = Module.search([("technical_name", "in", names)])
            record.depend_ids = depends
            record.depend_count = len(depends)
            record.depend_count_total = len(names)

    def _ext_prepare_vals_list(self, vals_list):
        def get_values(items, key):
            try:
                return list(set(map(itemgetter(key), items)))
            except KeyError:
                return []

        # Search or create all authors
        names = list(
            set(itertools.chain(*[vals.get("authors", []) for vals in vals_list]))
        )
        authors = self.env["catalog.author"].search_or_create(names) if names else False

        # Search or create all branches
        paths = get_values(vals_list, "branch")
        branches = self.env["catalog.branch"].search_or_create(paths)

        # Search or create all needed versions
        names = get_values(vals_list, "major_version")
        versions = self.env["catalog.version"].search_or_create(names)

        # Search or create categories
        names = get_values(vals_list, "category")
        categories = (
            self.env["catalog.category"].search_or_create(names) if names else False
        )

        exclude = [
            "authors",
            "major_version",
            "index",
            "icon",
            "branch_name",
            "addons_path",
        ]
        new_vals_list = []

        for vals in vals_list:
            if "data" in vals:
                vals["data"] = ", ".join(vals.get("data", []))

            if "depends" in vals:
                vals["depends"] = ", ".join(vals.get("depends", []))

            if authors and vals.get("authors"):
                # pylint: disable=E1101
                current_authors = authors.filtered_domain(
                    [("name", "in", vals["authors"])]
                )
                if current_authors:
                    vals["author_ids"] = [fields.Command.set(current_authors.ids)]

            if vals.get("branch"):
                res = branches.filtered_domain([("path", "=", vals["branch"])])
                vals["branch_id"] = res.id if res else False

            if vals.get("major_version"):
                res = versions.filtered_domain([("name", "=", vals["major_version"])])
                vals["version_id"] = res.id if res else False

            if categories and vals.get("category"):
                # pylint: disable=E1101
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
        _logger.warning("Update or Create - received: %s", len(vals_list))

        def set_parent(items, parent):
            def apply(item):
                item["catalog_module_id"] = parent
                return item

            return list(map(apply, items))

        entries = self
        vals_list = self._ext_prepare_vals_list(vals_list)

        mapping = {vals["uuid"]: vals for vals in vals_list}
        uuids = set(mapping.keys())
        data = self.search_read([("uuid", "in", list(uuids))], ["id", "uuid"], load="")

        to_update = {item["uuid"]: item["id"] for item in data}
        to_update_inverse = {str(item["id"]): item["uuid"] for item in data}

        uuid_to_create = uuids - set(to_update.keys())
        to_create = [vals for uuid, vals in mapping.items() if uuid in uuid_to_create]
        to_create = sorted(to_create, key=itemgetter("technical_name"))
        to_create = {
            i: list(g) for i, g in groupby(to_create, key=itemgetter("technical_name"))
        }

        _logger.warning("Update or Create [update]: %s", len(to_update))
        _logger.warning("Update or Create [create]: %s", len(uuid_to_create))

        if to_update:
            records = self.browse(to_update.values())

            for record in records:
                uuid = to_update_inverse.get(str(record.id))
                vals = mapping.get(uuid)
                record.write(vals)
                entries |= record

        if to_create:
            new_vals_list = []
            # Search for existing parents (catalog.module)
            # Technically, records on the current model with the catalog.defined module ID
            parents = self.search_read(
                [("technical_name", "in", list(to_create.keys()))],
                ["technical_name", "catalog_module_id"],
                load="",
            )
            # Create mapping by technical name
            parents = {
                item["technical_name"]: item["catalog_module_id"] for item in parents
            }

            for technical_name, vals_list in to_create.items():
                # Try to obtain the parent and associate it with the children (to avoid creating a duplicate parent)
                catalog_module_id = parents.get(technical_name)
                if catalog_module_id:
                    new_vals_list += set_parent(vals_list, catalog_module_id)
                # if this is not the case, create a parent with the values of the first child
                else:
                    new_record = self.create(vals_list[0])
                    entries |= new_record

                    # ...and associate it with his siblings
                    if len(vals_list) > 1:
                        new_vals_list += set_parent(
                            vals_list[1:], new_record.catalog_module_id.id
                        )

            # Finally, create all the other
            entries |= self.create(new_vals_list)

        return entries

    @api.model_create_multi
    def update_manifests(self, vals_list):
        vals_list = self._ext_prepare_vals_list(vals_list)

        records = self
        for vals in vals_list:
            if vals.get("id"):  # != 0
                record = self.browse(vals["id"])
            else:
                record = self.search([("uuid", "=", vals["uuid"])])

            if not record:
                _logger.error("Update manifest - Record not found: %s", vals["id"])
                continue

            vals["initialized"] = True
            record.write(vals)
            records |= record

        return records

    @api.model_create_multi
    def create(self, vals_list):
        # for vals in vals_list:
        #     self.catalog_module_id._sanitize_vals(vals)
        entries = super(
            CatalogEntry, self.with_context(create_catalog_entry=False)
        ).create(vals_list)
        # `_get_variant_id_for_combination` depends on existing variants
        self.env.registry.clear_cache()
        return entries

    def write(self, values):
        # self.catalog_module_id._sanitize_vals(values)
        res = super(CatalogEntry, self.with_context(create_catalog_entry=False)).write(
            values
        )
        if "active" in values:
            # `_get_first_possible_variant_id` depends on variants active state
            self.env.registry.clear_cache()
        return res

    def action_view_on_github(self):
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": self.module_url,
            "target": "new",
        }

    def action_view_modules(self):  # pylint: disable=C0116
        action = self.env.ref("catalog.action_view_modules").read()[0]
        action["domain"] = [("id", "in", self.depend_ids.ids)]

        return action

    def action_view_module(self):  # pylint: disable=C0116
        action = self.env.ref("catalog.action_view_modules").read()[0]
        # action["domain"] = [("id", "=", self.catalog_module_id.id)]
        action["res_id"] = self.catalog_module_id.id
        action["views"] = [(False, "form")]

        return action

    @api.model
    def get_icons(self, **kwargs):
        limit = kwargs.get("limit", 100)
        force = kwargs.get("force", False)

        if isinstance(force, str):
            force = eval(force)

        fields = ["icon_url"]

        domain = (
            [("icon_image", "=", ""), ("icon_url", "!=", "")]
            if not force
            else [("icon_url", "!=", "")]
        )
        # domain = []

        _logger.info("Fetch all entries: %s (%s)", domain, kwargs)
        results = self.env["catalog.entry"].search_read(
            domain, fields=fields, limit=limit, load=""
        )

        _logger.info("Get manifests - results/limit: %s/%s", len(results), limit)

        return results

    @api.model_create_multi
    def update_icons(self, vals_list):
        records = self
        for vals in vals_list:
            record = self.browse(vals["id"])

            if not record:
                _logger.error("Update manifest - Record not found: %s", vals["id"])
                continue

            record.write(vals)
            records |= record

        return records
