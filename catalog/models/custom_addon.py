import logging
import os

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CustomAddon(models.Model):
    _name = "custom.addon"
    _inherit = ["mail.thread", "mail.activity.mixin", "git.mixin"]
    _description = "Custom Addon"

    def _get_default_favorite_user_ids(self):
        # return [(6, 0, [self.env.uid])]
        return []

    name = fields.Char(required=True, index=True)
    description = fields.Text()
    web_description = fields.Html()
    summary = fields.Char()
    technical_name = fields.Char(required=True, index=True)
    application = fields.Boolean(default=False)
    depends = fields.Char()
    active = fields.Boolean(default=True)
    icon = fields.Char("Icon URL")
    icon_image = fields.Binary(string="Icon")
    url = fields.Char()
    # python_modules = fields.Char()

    version = fields.Char()
    # version_ids = fields.Many2many('custom.addon.version', string='Versions')
    version_ids = fields.One2many(
        comodel_name="custom.addon.version",
        compute="_compute_versions",
        string="Versions",
        search="_search_versions",
    )
    author = fields.Char()
    partner_id = fields.Many2one(comodel_name="res.partner")
    user_id = fields.Many2one(comodel_name="res.users")
    category_id = fields.Many2one(comodel_name="ir.module.category")
    category = fields.Char(string="Category (original)")
    last_sync_date = fields.Datetime(readonly=True)

    tag_ids = fields.Many2many("custom.addon.tags", string="Tags")

    branch_ids = fields.Many2many(
        string="Branches",
        comodel_name="git.branch",
        relation="git_branch_custom_addon_rel",
        column1="custom_addon_id",
        column2="branch_id",
    )

    branch_count = fields.Integer(
        compute="_compute_branch", store=True, compute_sudo=True, string="# Branches"
    )
    repository_count = fields.Integer(
        compute="_compute_branch", store=True, compute_sudo=True, string="# Repository"
    )
    is_many_used = fields.Boolean(
        compute="_compute_branch", store=True, compute_sudo=True, string="Many Used"
    )
    color = fields.Integer(
        compute="_compute_branch", compute_sudo=True, string="Color Index"
    )

    favorite_user_ids = fields.Many2many(
        "res.users",
        "custom_addons_favorite_user_rel",
        default=_get_default_favorite_user_ids,
        string="Members",
    )
    is_favorite = fields.Boolean(
        compute="_compute_is_favorite",
        inverse="_inverse_is_favorite",
        string="Show Project on dashboard",
    )

    @api.depends("branch_ids")
    def _compute_versions(self):
        version_env = self.env["custom.addon.version"]
        for record in self:
            # record.version_ids = record.branch_ids.filtered(lambda x: x.major).mapped('version_id')
            names = list(
                set(record.branch_ids.filtered(lambda x: x.major).mapped("name"))
            )
            record.version_ids = version_env.search([("name", "in", names)])

    def _search_versions(self, operator, value):
        return [("branch_ids.name", operator, value)]

    def _compute_is_favorite(self):
        for record in self:
            record.is_favorite = self.env.user in record.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_addons = not_fav_addons = self.env["custom.addon"].sudo()
        for record in self:
            if self.env.user in record.favorite_user_ids:
                favorite_addons |= record
            else:
                not_fav_addons |= record

        not_fav_addons.write({"favorite_user_ids": [(4, self.env.uid)]})
        favorite_addons.write({"favorite_user_ids": [(3, self.env.uid)]})

    # @api.depends('branch_ids')
    # def _compute_url(self):
    #     for record in self:
    #         record.url = os.path.join(record.branch_ids[0].url, record.technical_name) if record.branch_ids else ""

    @api.depends("branch_ids")
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.repository_count = len(record.branch_ids.mapped("repository_id"))
            record.is_many_used = record.repository_count > 1
            record.color = 1 if record.is_many_used else 0

    def _action_view_git_branch(self, action):
        action["domain"] = [("id", "in", self.branch_ids.ids)]

        return action

    def _action_view_git_repository(self, action):
        repo_ids = self.branch_ids.mapped("repository_id").ids
        action["domain"] = [("id", "in", repo_ids)]

        return action

    def action_open_url(self):
        self.ensure_one()
        action = super().action_open_url()
        res_id = self.env.context.get("branch_id")

        if res_id:
            branch = self.env["git.branch"].browse(res_id)
            parts = [branch.url, branch.repository_id.subfolder, self.technical_name]
            # if self.repository_id.subfolder:
            #     parts.insert(1, self.repository_id.subfolder)
            action["url"] = os.path.join(*parts)
        else:
            action["url"] = None

        return action
