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
    repository_id = fields.Many2one(
        comodel_name="catalog.repository",
        ondelete="cascade",
    )
    organization_id = fields.Many2one(
        related="repository_id.organization_id",
    )

    _sql_constraints = [
        (
            "path_uniq",
            "unique (path)",
            "Path already exists !",
        ),
    ]

    def _prepare_vals(self, path):
        org, repo, name = path.split("/")
        vals = {
            "name": name,
            "path": path,
            "repository_id": "/".join(org, repo),
        }

        return vals

    @api.model
    def search_or_create(self, paths):
        Organization = self.env["catalog.organization"]

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
