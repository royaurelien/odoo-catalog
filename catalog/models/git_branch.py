# -*- coding: utf-8 -*-


from datetime import datetime
import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)

RECENT_ACTIVITY_DAYS = 30
COMMIT_MESSAGE = (
    "{o[last_commit_message]}, {o[last_commit_author]} ({o[last_commit_short_id]})"
)
COMMIT_VARS = [
    "last_commit_message",
    "last_commit_author",
    "last_commit_short_id",
    "last_commit_url",
    "last_commit_date",
]

MESSAGES = {"new_branch": "Found {} from {} repository."}


class GitBranch(models.Model):
    _name = "git.branch"
    _inherit = ["mail.thread", "mail.activity.mixin", "git.sync", "git.mixin"]
    _description = "Git Branch"
    _order = "last_sync_date desc, name desc"

    ### GIT ###
    _git_service = "service"
    _git_field_rel = "custom_addon_ids"
    _git_field_name = "technical_name"
    _git_type_rel = "m2m"
    _git_parent_field = "repository_id"

    last_commit_message = fields.Char()
    last_commit_author = fields.Char()
    last_commit_short_id = fields.Char()
    last_commit_url = fields.Char()
    last_commit_date = fields.Datetime()
    last_commit = fields.Char(compute="_compute_commit", store=True)
    is_recent_activity = fields.Boolean(
        compute="_compute_commit", string="Recent Activity", store=True
    )

    force_partner = fields.Boolean(related="repository_id.force_partner")

    @api.depends(
        "last_commit_message",
        "last_commit_author",
        "last_commit_date",
        "last_sync_date",
    )
    def _compute_commit(self):
        now = datetime.now()
        for record in self:
            vals = record.read(COMMIT_VARS)[0]
            record.last_commit = COMMIT_MESSAGE.format(o=vals)
            record.is_recent_activity = False

            if record.last_sync_date and record.last_commit_date:
                if (now - record.last_commit_date).days <= RECENT_ACTIVITY_DAYS:
                    record.is_recent_activity = True

    major = fields.Boolean(default=False)
    requirements = fields.Boolean(default=False)
    python_modules = fields.Char()
    odoo_version = fields.Char()

    # version_id = fields.Many2one(comodel_name='custom.addon.version')
    repository_id = fields.Many2one(comodel_name="git.repository", ondelete="cascade")
    organization_id = fields.Many2one(
        related="repository_id.organization_id", store=True, ondelete="cascade"
    )
    service = fields.Selection(
        related="repository_id.organization_id.service", store=True
    )
    sync_identifier = fields.Char(
        related="repository_id.organization_id.sync_identifier", store=True
    )
    user_id = fields.Many2one(comodel_name="res.users")
    path = fields.Char(related="repository_id.path", store=True)
    git_clone_command = fields.Char(
        compute="_compute_clone_command", string="Clone Command"
    )

    tag_ids = fields.Many2many("custom.addon.tags", string="Tags")

    custom_addon_ids = fields.Many2many(
        string="Custom Addons",
        comodel_name="custom.addon",
        relation="git_branch_custom_addon_rel",
        column1="branch_id",
        column2="custom_addon_id",
        tracking=True,
    )

    custom_addon_count = fields.Integer(compute="_compute_custom_addon", store=True)

    commit_ids = fields.One2many(
        comodel_name="git.commit.items", inverse_name="branch_id"
    )
    commit_count = fields.Integer(compute="_compute_commit", compute_sudo=True)

    @api.depends("commit_ids")
    def _compute_commit(self):
        for record in self:
            record.commit_count = len(record.commit_ids)

    @api.depends("repository_id.http_git_url", "sync_identifier")
    def _compute_clone_command(self):
        command = "git clone --depth=1 {}"
        for record in self:
            command = record.repository_id.git_clone_command
            if not command:
                record.git_clone_command = False
                continue

            record.git_clone_command = (
                f"{command} --branch {record.name} --single-branch"
            )

    @api.depends("custom_addon_ids")
    def _compute_custom_addon(self):
        for record in self:
            record.custom_addon_count = len(record.custom_addon_ids)

    def _action_view_custom_addons(self, action):
        action["domain"] = [("id", "in", self.custom_addon_ids.ids)]
        return action

    def _action_view_git_commits(self, action):
        action["domain"] = [("id", "in", self.commit_ids.ids)]
        return action

    @api.model_create_multi
    def create(self, vals_list):
        res_ids = super().create(vals_list)
        names = res_ids.filtered(lambda x: x.major).mapped("name")

        # FIXME : res of search_or_create not used ?
        versions = self.env["custom.addon.version"].search_or_create(names)
        _logger.debug(versions)

        return res_ids
