import logging

from odoo import _, fields, models

_logger = logging.getLogger(__name__)


class GitOrganization(models.Model):
    _inherit = "git.organization"

    allow_repository_create = fields.Boolean(
        default=False, string="Allow repository create"
    )
    allow_branch_create = fields.Boolean(default=False, string="Allow branch create")

    workflow = fields.Selection([("odoo", "Odoo")], string="Git Workflow")
    default_visibility = fields.Selection(
        [("public", "Public"), ("internal", "Internal"), ("private", "Private")],
        string="Default visibility",
    )
    default_namespace_id = fields.Many2one(
        comodel_name="git.namespace", string="Default namespace"
    )

    namespace_ids = fields.One2many(
        comodel_name="git.namespace",
        inverse_name="organization_id",
        string="Namespaces",
    )

    def action_update(self):
        vals_list = self._get_namespaces_for_odoo()

        namespace_ids = self.namespace_ids.mapped("namespace_id")
        to_create = list(
            filter(lambda item: item["namespace_id"] not in namespace_ids, vals_list)
        )

        if to_create:
            self.write({"namespace_ids": [(0, False, vals) for vals in to_create]})

        return True

    def action_create_repository(self):
        view_id = self.env.ref("catalog_developper.create_repository_view_form").id
        vals = {
            "organization_id": self.id,
            "branch_create": self.allow_branch_create,
            "visibility": self.default_visibility,
            "namespace_id": self.default_namespace_id.id,
        }

        wizard = self.env["catalog.create.repository"].create(vals)

        return {
            "name": _("New repository"),
            "view_mode": "form",
            "res_model": "catalog.create.repository",
            "view_id": view_id,
            "views": [(view_id, "form")],
            "type": "ir.actions.act_window",
            "res_id": wizard.id,
            "target": "new",
        }
