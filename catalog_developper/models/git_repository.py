import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _inherit = "git.repository"

    allow_repository_create = fields.Boolean(
        related="organization_id.allow_repository_create"
    )
    allow_branch_create = fields.Boolean(related="organization_id.allow_branch_create")

    def action_create_branch(self):
        view_id = self.env.ref("catalog_developper.create_branch_view_form").id
        branch_id = self.branch_ids.filtered_domain(
            [("name", "=", self.default_branch)]
        )
        vals = {
            "organization_id": self.organization_id.id,
            "repository_id": self.id,
            "namespace_id": self.organization_id.default_namespace_id.id,
            "branch_id": branch_id[0].id if branch_id else False,
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
