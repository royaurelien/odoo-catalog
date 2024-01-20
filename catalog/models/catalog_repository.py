import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogRepository(models.Model):
    _name = "catalog.repository"
    _description = "Catalog repository"
    _order = "name, id"

    name = fields.Char(
        required=True,
        index=True,
    )
    path = fields.Char(
        required=True,
        index=True,
    )
    description = fields.Char()
    visibility = fields.Selection(
        selection=[("private", "Private"), ("public", "Public")],
        default="public",
        required=True,
    )
    default_branch = fields.Char()
    ext_id = fields.Char()
    git_url = fields.Char()
    ssh_url = fields.Char()
    created_at = fields.Datetime()
    updated_at = fields.Datetime()
    pushed_at = fields.Datetime()

    organization_id = fields.Many2one(
        comodel_name="catalog.organization",
        ondelete="cascade",
    )
    branch_ids = fields.One2many(
        comodel_name="catalog.branch",
        inverse_name="repository_id",
    )
    branch_count = fields.Integer(
        compute="_compute_branch",
    )

    _sql_constraints = [
        (
            "path_uniq",
            "unique (path)",
            "Path already exists !",
        ),
    ]

    def _get_fields(self):
        return [
            "name",
            "path",
            "description",
            "visibility",
            "default_branch",
            "ext_id",
            "git_url",
            "ssh_url",
            "created_at",
            "updated_at",
            "pushed_at",
            "organization_id",
            "branch_ids",
        ]

    @api.depends("branch_ids")
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)

    def _prepare_vals(self, path):
        vals = {
            "name": path.split("/")[-1],
            "path": path,
        }

        return vals

    def _sanitize_vals(self, vals):
        if "id" in vals:
            vals["ext_id"] = vals.pop("id")
        if "organization" in vals:
            path = vals.pop("organization")
            res = self.env["catalog.organization"].get_or_create(path)
            vals["organization_id"] = res.id

        vals = {k: v for k, v in vals.items() if k in self._get_fields()}

        return vals

    @api.model
    def get_or_create(self, path):
        record = self.search([("path", "=", path)], limit=1)

        if not record:
            record = self.create(self._prepare_vals(path))

        return record

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = list(map(self._sanitize_vals, vals_list))
        repositories = super().create(vals_list)

        return repositories

    def write(self, vals):
        vals = self._sanitize_vals(vals)
        return super().write(vals)

    @api.model_create_multi
    def update_or_create(self, vals_list):
        mapping = {vals["path"]: vals for vals in vals_list}
        paths = list(mapping.keys())
        records = self.search([("path", "in", paths)])
        not_updated = self
        current_paths = records.mapped("path")

        to_create = [mapping.get(path) for path in paths if path not in current_paths]
        to_update = [mapping.get(path) for path in paths if path in current_paths]

        if to_create:
            records |= self.create(to_create)

        if to_update:
            for vals in to_update:
                record = records.filtered_domain([("path", "=", vals["path"])])
                if not record:
                    not_updated |= record

                record.write(vals)

        return records - not_updated

    # @api.model
    # def search_or_create(self, paths):
    #     _logger.error(paths)
    #     records = self.search([("path", "in", paths)])
    #     current_paths = records.mapped("path")
    #     to_create = [path for path in paths if path not in current_paths]
    #     to_create = list(map(self._prepare_vals, to_create))

    #     if to_create:
    #         records |= self.create(to_create)

    #     return records

    def action_view_branches(self):  # pylint: disable=C0116
        action = self.env.ref("catalog.action_view_branches").read()[0]
        action["domain"] = [("id", "in", self.branch_ids.ids)]

        return action
