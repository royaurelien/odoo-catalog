from odoo import _, models


class GitBranch(models.Model):
    _inherit = "git.branch"

    def action_duplicate(self):
        if not self.repository_id.allow_branch_create:
            return False

        view_id = self.env.ref("catalog_developper.create_branch_view_form").id
        vals = {
            "organization_id": self.organization_id.id,
            "repository_id": self.repository_id.id,
            "namespace_id": self.organization_id.default_namespace_id.id,
            "branch_id": self.id,
        }

        wizard = self.env["catalog.create.branch"].create(vals)

        return {
            "name": _("New branch"),
            "view_mode": "form",
            "res_model": "catalog.create.branch",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "target": "new",
        }
