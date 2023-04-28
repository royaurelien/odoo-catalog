import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class GitRepository(models.Model):
    _name = "git.repository"
    _inherit = ["mail.thread", "mail.activity.mixin", "git.sync", "git.mixin"]
    _description = "Git Repository"

    def _get_default_favorite_user_ids(self):
        # return [(6, 0, [self.env.uid])]
        return []

    ### GIT ###
    _git_service = "service"
    _git_field_rel = "branch_ids"
    _git_field_name = "name"
    _git_type_rel = "o2m"
    _git_parent_field = "organization_id"

    path = fields.Char(required=True)
    subfolder = fields.Char()
    description = fields.Char()
    repo_id = fields.Integer(string="Repository ID")
    http_git_url = fields.Char(string="HTTP Url")
    ssh_git_url = fields.Char(string="SSH Url")
    git_clone_command = fields.Char(
        compute="_compute_clone_command", string="Clone Command"
    )

    force_partner = fields.Boolean(related="organization_id.force_partner")

    repository_create_date = fields.Datetime(readonly=True)
    repository_update_date = fields.Datetime(readonly=True, tracking=True)

    default_branch = fields.Char()

    user_id = fields.Many2one(comodel_name="res.users")
    organization_id = fields.Many2one(
        comodel_name="git.organization",
        index=True,
        readonly=True,
        ondelete="cascade",
    )
    service = fields.Selection(related="organization_id.service", store=True)
    sync_identifier = fields.Char(related="organization_id.sync_identifier", store=True)
    branch_ids = fields.One2many(
        comodel_name="git.branch", inverse_name="repository_id"
    )

    branch_count = fields.Integer(
        compute="_compute_branch", store=True, compute_sudo=True, string="# Branches"
    )
    branch_major_count = fields.Integer(
        compute="_compute_branch",
        compute_sudo=True,
        store=True,
        string="# Major Branches",
    )
    custom_addon_count = fields.Integer(
        compute="_compute_branch", compute_sudo=True, string="# Addons"
    )

    tag_ids = fields.Many2many("custom.addon.tags", string="Tags")
    color = fields.Integer(compute="_compute_color")

    is_favorite = fields.Boolean(
        compute="_compute_is_favorite", inverse="_inverse_is_favorite"
    )
    favorite_user_ids = fields.Many2many(
        "res.users",
        "git_repository_favorite_user_rel",
        default=_get_default_favorite_user_ids,
        string="Members",
    )

    # commit_ids = fields.One2many(comodel_name='git.commit.items', compute='_compute_commit')
    commit_ids = fields.One2many(
        comodel_name="git.commit.items", inverse_name="repository_id"
    )
    commit_count = fields.Integer(compute="_compute_commit")

    contributor_ids = fields.Many2many(
        string="Contributors",
        comodel_name="git.contributor",
        relation="git_repository_contributor_rel",
        column1="contributor_id",
        column2="repository_id",
        tracking=True,
    )

    contributor_count = fields.Integer(compute="_compute_contributor", store=True)

    @api.depends("contributor_ids")
    def _compute_contributor(self):
        for record in self:
            record.contributor_count = len(record.contributor_ids)

    @api.depends("commit_ids")
    def _compute_commit(self):
        for record in self:
            record.commit_count = len(record.commit_ids)

    def _compute_is_favorite(self):
        for record in self:
            record.is_favorite = self.env.user in record.favorite_user_ids

    def _inverse_is_favorite(self):
        favorite_addons = not_fav_addons = self.env["git.repository"].sudo()
        for record in self:
            if self.env.user in record.favorite_user_ids:
                favorite_addons |= record
            else:
                not_fav_addons |= record

        not_fav_addons.write({"favorite_user_ids": [(4, self.env.uid)]})
        favorite_addons.write({"favorite_user_ids": [(3, self.env.uid)]})

    @api.depends("http_git_url", "sync_identifier")
    def _compute_clone_command(self):
        command = "git clone --depth=1 {}"
        for record in self:
            if not record.organization_id or not record.http_git_url:
                record.git_clone_command = False
                continue

            auth = record.organization_id.auth_id

            # Private: token + login or login + password
            if (auth.auth_method == "token" and auth.login) or (
                auth.auth_method == "basic"
            ):
                credentials = f"://{auth.login}:{auth.token if auth.auth_method == 'token' else auth.password}@"
                record.git_clone_command = command.format(
                    record.http_git_url.replace("://", credentials)
                )
            # Public
            else:
                record.git_clone_command = command.format(record.http_git_url)

    @api.depends("is_synchronized")
    def _compute_color(self):
        for record in self:
            record.color = 1 if record.is_synchronized else 0

    @api.depends("branch_ids")
    def _compute_branch(self):
        for record in self:
            record.branch_count = len(record.branch_ids)
            record.branch_major_count = len(
                record.branch_ids.filtered(lambda x: x.major)
            )
            record.custom_addon_count = len(
                record.branch_ids.mapped("custom_addon_ids")
            )

    def _action_view_git_branch(self, action):
        action["context"]["search_default_repository_id"] = self.id
        action["domain"] = [("repository_id", "=", self.id)]

        return action

    def _action_view_custom_addons(self, action):
        action["domain"] = [
            ("id", "in", self.branch_ids.mapped("custom_addon_ids").ids)
        ]

        return action

    def _action_view_git_commits(self, action):
        action["domain"] = [("id", "in", self.commit_ids.ids)]

        return action

    def _action_view_git_contributor(self, action):
        action["domain"] = [("id", "in", self.contributor_ids.ids)]

        return action

    def action_ignore(self):
        for organization_id in self.mapped("organization_id"):
            records = self.filtered(lambda rec: rec.organization_id == organization_id)
            excludes = organization_id._get_excludes()
            excludes = list(set(excludes + records.mapped("path")))
            organization_id.update({"exclude_names": ", ".join(excludes)})
            records.update({"is_synchronized": False})

        return True
