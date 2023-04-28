from odoo import fields, models


class GitNamespace(models.Model):
    _name = "git.namespace"
    _description = "Git Namespace"

    name = fields.Char(required=True)
    namespace_id = fields.Char(required=True)
    organization_id = fields.Many2one("git.organization")
    active = fields.Boolean(default=True)
