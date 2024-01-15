import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogAuthor(models.Model):
    _name = "catalog.author"
    _description = "Catalog Author"
    _order = "name, id"

    name = fields.Char(required=True)

    @api.model
    def search_or_create(self, names):
        authors = self.search([("name", "in", names)])
        to_create = [name for name in names if name not in authors.mapped("name")]

        if to_create:
            authors |= self.create([{"name": name} for name in to_create])

        return authors
