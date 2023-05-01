from odoo import _, api, fields, models
from odoo.addons.http_routing.models.ir_http import slugify

# from odoo.tools.float_utils import float_compare


class CreateRepository(models.TransientModel):
    _name = "catalog.create.repository"
    _description = "Create Repository"

    organization_id = fields.Many2one(comodel_name="git.organization")
    name = fields.Char()
    path = fields.Char()
    namespace_id = fields.Many2one(comodel_name="git.namespace", string="Namespace")
    description = fields.Char()
    visibility = fields.Selection(
        [("public", "Public"), ("internal", "Internal"), ("private", "Private")]
    )
    odoo_version = fields.Selection(selection="_selection_version")

    branch_create = fields.Boolean(default=False)
    branch_name = fields.Char()
    second_branch_create = fields.Boolean(default=False)
    second_branch_name = fields.Char()

    @api.model
    def _selection_version(self):
        versions = self.env["custom.addon.version"].search([]).mapped("name")
        return list(map(lambda x: (x, x), versions))

    @api.onchange("odoo_version")
    def _onchange_version(self):
        if self.odoo_version:
            self.branch_name = self.odoo_version
            self.second_branch_name = "{}-test".format(self.branch_name)
        else:
            self.branch_name = ""
            self.second_branch_name = ""

    @api.onchange("name")
    def _onchange_name(self):
        if self.name:
            self.path = slugify(self.name)
        else:
            self.path = ""

    def validate(self):
        vals = {
            "name": self.name,
            "path": self.path,
            "namespace_id": self.namespace_id.namespace_id,
            "description": self.description,
            "visibility": self.visibility,
        }

        if self.branch_create and self.branch_name:
            vals["branch_name"] = self.branch_name

        repository = self.organization_id._create_repository_from_odoo(vals)

        if repository:
            if self.second_branch_create and self.second_branch_name:
                repository._create_branch_from_odoo(
                    {"branch": self.second_branch_name, "ref": self.branch_name},
                    force_create=True,
                )
            repository.action_sync()

            return self.organization_id.action_view_git_repository(res_id=repository.id)

        return False
