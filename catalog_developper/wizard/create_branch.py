from odoo import fields, models

# from odoo.addons.http_routing.models.ir_http import slugify


class CreateBranch(models.TransientModel):
    _name = "catalog.create.branch"
    _description = "Create Branch"

    organization_id = fields.Many2one(comodel_name="git.organization")
    repository_id = fields.Many2one(comodel_name="git.repository")
    branch_id = fields.Many2one(comodel_name="git.branch")
    namespace_id = fields.Many2one(comodel_name="git.namespace")
    name = fields.Char()

    def validate(self):
        if not self.repository_id:
            return False

        self.repository_id._create_branch_from_odoo(
            {"branch": self.name, "ref": self.branch_id.name}
        )
        self.repository_id.action_sync()

        branch = self.repository_id.branch_ids.filtered_domain(
            [("name", "=", self.name)]
        )
        options = {"res_id": branch[0].id if branch else False}

        return self.organization_id.action_view_git_branch(**options)
