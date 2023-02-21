# -*- coding: utf-8 -*-

import logging
import re

from github import (
    Github,
    RateLimitExceededException,
    UnknownObjectException,
    BadCredentialsException,
)

from odoo import models, fields, _
from odoo.exceptions import UserError


REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TYPE = [("github", "Github")]

_logger = logging.getLogger(__name__)


class GitOrganization(models.Model):
    _inherit = "git.organization"

    service = fields.Selection(selection_add=TYPE)

    def _get_github(self):
        self.ensure_one()
        org = None

        try:
            conn = Github(self.auth_id.token)
            limit = conn.get_rate_limit()
        except BadCredentialsException as error:
            _logger.error(error)
            raise UserError(_("Bad Credentials"))

        rate_limit = "Remaining {o.remaining}/{o.limit}, Reset at {o.reset}.".format(
            o=limit.core
        )
        _logger.warning(rate_limit)

        try:
            org = (
                conn.get_user(self.name)
                if self.is_user
                else conn.get_organization(self.name)
            )
        except UnknownObjectException as error:
            _logger.error(error)
            raise UserError(f"{error.data.get('message')}\n{rate_limit}")
        except RateLimitExceededException as error:
            _logger.error(error)
            raise UserError(f"{error.data.get('message')}\n{rate_limit}")

        # if self.enable_debug:
        #     try:
        #         conn.enable_console_debug_logging()
        #     except Exception as error:
        #         _logger.error(error)

        return org

    def _get_items_from_github(self):
        self.ensure_one()
        org = self._get_github()
        repositories = org.get_repos()

        # return [repo for repo in repos]
        return self._filter_from_github(repositories)

    def _filter_from_github(self, repositories):
        excludes = self._get_excludes()
        return [repo for repo in repositories if repo.name not in excludes]

    def _convert_github_to_odoo(self, item, **kwargs):
        vals = {
            "organization_id": self.id,
            "repo_id": item.id,
            "name": item.full_name,
            "path": item.name,
            "description": item.description,
            "url": item._html_url.value,
            "http_git_url": item.clone_url,
            "ssh_git_url": item.git_url,
            "default_branch": item.default_branch,
            "repository_create_date": item.created_at,
            "repository_update_date": item.updated_at,
        }

        return vals
