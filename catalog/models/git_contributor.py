from odoo import fields, models


class GitContributor(models.Model):
    _name = "git.contributor"
    _description = "Git Contributor"

    name = fields.Char()
    email = fields.Char()
    repository_id = fields.Many2one("git.repository")
