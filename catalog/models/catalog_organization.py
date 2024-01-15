import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogOrganization(models.Model):
    _name = "catalog.organization"
    _description = "Catalog Organization"
    _order = "name, id"

    name = fields.Char(
        required=True,
        index=True,
    )
    path = fields.Char(
        required=True,
        index=True,
    )
    repository_ids = fields.One2many(
        comodel_name="catalog.repository",
        inverse_name="organization_id",
    )

    _sql_constraints = [
        (
            "name_uniq",
            "unique (name)",
            "Name already exists !",
        ),
    ]

    def _prepare_vals(self, name):
        return {
            "name": name,
        }

    # @api.model
    # def search_or_create(self, names):
    #     records = self.search([("name", "in", names)])
    #     current_names = records.mapped("name")
    #     to_create = [name for name in names if name not in current_names]
    #     to_create = list(map(self._prepare_vals, to_create))

    #     if to_create:
    #         records |= self.create(to_create)

    #     return records

    @api.model
    def _create_from_path(self, path):
        name, repository, branch = path.split("/")
        record = self.search([("name", "=", name)])

        if not record:
            record = self.create(self._prepare_vals(name))

        if repository not in record.repository_ids.mapped("name"):
            path = "/".join(name, repository)
            vals = record.repository_ids._prepare_vals(path)
            record.repository_ids = [fields.Command.create(vals)]

        return record

    @api.model
    def create_from_path(self, paths):
        records = self
        for path in paths:
            records |= self._create_from_path(path)
        return records

    def get_mapping(self):
        return {res.path: res.id for res in self.repository_ids}
