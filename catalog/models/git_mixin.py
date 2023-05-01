from odoo import fields, models


XML_ACTIONS = {
    "custom_addons": "catalog.action_view_addons",
    "git_branch": "catalog.action_view_branch",
    "git_repository": "catalog.action_view_repository",
    "git_organization": "catalog.action_view_organization",
    "git_commits": "catalog.action_view_commits",
    "git_contributor": "catalog.action_view_contributor",
}


class GitMixin(models.AbstractModel):
    _name = "git.mixin"
    _description = "Git Mixin"

    note = fields.Html()
    origin = fields.Char(tracking=True)

    def action_open_url(self):
        self.ensure_one()
        # url = getattr(self, 'url') if hasattr(self, 'url') else None
        action = {
            "type": "ir.actions.act_url",
            "url": self.url,
            "target": "new",
        }

        return action

    def _get_xml_action(self, name):
        ref = XML_ACTIONS.get(name)
        return self.env.ref(ref).sudo().read()[0]

    def _action_view(self, name, **kwargs):
        action = self._get_xml_action(name)
        action["context"] = dict(self.env.context)

        action.update(kwargs)

        method = getattr(self, f"_action_view_{name}")
        action = method(action)

        res_id = kwargs.get("res_id", False)

        # switch to form view if only one record
        if action["domain"] and action["domain"][0][0] == "id":
            items = action["domain"][0][2]

            if len(items) == 1:
                action["res_id"] = items[0]
                action["views"] = [(False, "form")]
        elif res_id:
            # action['domain'] = []
            action["res_id"] = res_id
            action["views"] = [(False, "form")]

        return action

    def action_view_git_repository(self, **kwargs):
        return self._action_view("git_repository", **kwargs)

    def action_view_git_branch(self, **kwargs):
        return self._action_view("git_branch", **kwargs)

    def action_view_git_organization(self):
        return self._action_view("git_organization")

    def action_view_custom_addons(self):
        return self._action_view("custom_addons")

    def action_view_commits(self):
        return self._action_view("git_commits", context=dict(create=False))

    def action_view_contributor(self):
        return self._action_view("git_contributor", context=dict(create=False))
