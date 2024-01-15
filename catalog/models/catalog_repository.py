import logging

from odoo import fields, models

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
    organization_id = fields.Many2one(
        comodel_name="catalog.organization",
    )
    branch_ids = fields.One2many(
        comodel_name="catalog.branch",
        inverse_name="repository_id",
    )

    _sql_constraints = [
        (
            "path_uniq",
            "unique (path)",
            "Path already exists !",
        ),
    ]

    def _prepare_vals(self, path):
        vals = {
            "name": path.split("/")[-1],
            "path": path,
        }

        return vals

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
