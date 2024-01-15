import logging
from random import randint

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CatalogVersion(models.Model):
    _name = "catalog.version"
    _description = "Catalog Version"
    _order = "name, id"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(
        required=True,
    )
    color = fields.Integer(
        "Color",
        default=_get_default_color,
    )

    @api.model
    def search_or_create(self, names):
        authors = self.search([("name", "in", names)])
        to_create = [name for name in names if name not in authors.mapped("name")]

        if to_create:
            authors |= self.create([{"name": name} for name in to_create])

        return authors
