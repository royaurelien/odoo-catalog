import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogBranch(models.Model):
    _name = "catalog.branch"
    _description = "Catalog Branch"
    _order = "name, id"

    name = fields.Char(
        required=True,
        index=True,
    )
    path = fields.Char(
        required=True,
        index=True,
    )
    html_url = fields.Char()
    tree_url = fields.Char()
    entry_ids = fields.One2many(
        comodel_name="catalog.entry",
        inverse_name="branch_id",
    )
    repository_id = fields.Many2one(
        comodel_name="catalog.repository",
        ondelete="cascade",
    )
    organization_id = fields.Many2one(
        related="repository_id.organization_id",
        store=True,
    )
    entry_count = fields.Integer(
        compute="_compute_entry",
    )
    initialized = fields.Boolean(
        default=False,
    )

    last_commit_url = fields.Char(string="Commit Url")
    last_commit_name = fields.Char(string="Author")
    last_commit_email = fields.Char(string="Email")
    last_commit_date = fields.Datetime(string="Last Commit")

    _sql_constraints = [
        (
            "path_uniq",
            "unique (path)",
            "Path already exists !",
        ),
    ]

    @api.depends("entry_ids")
    def _compute_entry(self):
        for record in self:
            record.entry_count = len(record.entry_ids)

    def _prepare_vals(self, path):
        org, repo, name = path.split("/")
        vals = {
            "name": name,
            "path": path,
            "repository_id": "/".join([org, repo]),
        }

        return vals

    def _get_fields(self):
        return [
            "name",
            "path",
            "html_url",
            "tree_url",
            "entry_ids",
            "repository_id",
            "organization_id",
            "initialized",
            "last_commit_url",
            "last_commit_name",
            "last_commit_email",
            "last_commit_date",
        ]

    @api.model
    def search_or_create(self, paths):
        Organization = self.env["catalog.organization"]  # pylint: disable=C0103

        records = self.search([("path", "in", paths)])
        current_paths = records.mapped("path")
        to_create = list(
            map(
                self._prepare_vals,
                filter(lambda path: path not in current_paths, paths),
            )
        )

        if to_create:
            organizations = Organization.create_from_path(paths)
            mapping = organizations.get_mapping()
            vals_list = []
            for vals in to_create:
                repository_id = mapping.get(vals["repository_id"], False)
                vals["repository_id"] = repository_id
                vals_list.append(vals)

            records |= self.create(vals_list)

        return records

    def _sanitize_vals(self, vals):
        if "repository" in vals:
            parts = vals["path"].split("/")
            path = "/".join(parts[0:2])
            res = self.env["catalog.repository"].get_or_create(path)
            vals["repository_id"] = res.id

        vals = {k: v for k, v in vals.items() if k in self._get_fields()}

        return vals

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = list(map(self._sanitize_vals, vals_list))
        repositories = super().create(vals_list)

        return repositories

    @api.model_create_multi
    def update_or_create(self, vals_list):
        mapping = {vals["path"]: vals for vals in vals_list}
        paths = list(mapping.keys())
        records = self.search([("path", "in", paths)])
        current_paths = records.mapped("path")

        to_create = [mapping.get(path) for path in paths if path not in current_paths]

        if to_create:
            records |= self.create(to_create)

        return records

    def action_view_entries(self):  # pylint: disable=C0116
        action = self.env.ref("catalog.action_view_entries").read()[0]
        action["domain"] = [("id", "in", self.entry_ids.ids)]

        return action

    @api.model
    def get_branches(self, **kwargs):
        limit = kwargs.get("limit", 100)
        force = kwargs.get("force", False)
        domain = []

        if not force:
            domain = [("initialized", "=", False)]

        res = self.search_read(
            domain,
            fields=["name", "path"],
            limit=limit,
            load="",
        )

        _logger.info("Get branches - results/limit: %s/%s", len(res), limit)

        return res

    @api.model_create_multi
    def update_branches(self, vals_list):
        vals_list = list(map(self._sanitize_vals, vals_list))

        records = self
        for vals in vals_list:
            if vals.get("id"):  # != 0
                record = self.browse(vals["id"])
            else:
                record = self.search([("path", "=", vals["path"])])

            if not record:
                _logger.error("Update branch - Record not found: %s", vals["id"])
                continue

            vals["initialized"] = True
            record.write(vals)
            records |= record

        return records
