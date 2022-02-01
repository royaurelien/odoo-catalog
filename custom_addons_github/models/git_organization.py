# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api
from odoo.tools import datetime
from odoo.exceptions import ValidationError, UserError

from datetime import datetime
from github import Github, GithubException, RateLimitExceededException, UnknownObjectException
import logging
import re
import os

REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TYPE = [('github', 'Github')]

_logger = logging.getLogger(__name__)

class GitOrganization(models.Model):
    _inherit = 'git.organization'

    service = fields.Selection(selection_add=TYPE)

    def _get_github(self):

        self.ensure_one()
        org = None
        g = Github(self.token)
        limit = g.get_rate_limit()
        rate_limit = "Remaining {o.remaining}/{o.limit}, Reset at {o.reset}.".format(o=limit.core)
        _logger.warning(limit.core)

        try:
            org = g.get_user(self.name) if self.is_user else g.get_organization(self.name)
        except UnknownObjectException as error:
            _logger.error(error)
            raise UserError("{}\n{}".format(error.data.get('message'), rate_limit))
        except RateLimitExceededException as error:
            _logger.error(error)
            raise UserError("{}\n{}".format(error.data.get('message'), rate_limit))

        return org

    def _get_items_from_github(self):
        self.ensure_one()
        org = self._get_github()
        repos = org.get_repos()
        # excludes = self.exclude_names.strip().split(",")
        return [repo for repo in repos]
        # return [repo for repo in repos if repo.name not in excludes]

    def _convert_github_to_odoo(self, item):
        vals = {
            'organization_id': self.id,
            'repo_id': item.id,
            'name': item.full_name,
            'path': item.name,
            'description': item.description,
            'url': item._html_url.value,
            'http_git_url' : item.clone_url,
            'ssh_git_url' : item.git_url,
            'default_branch': item.default_branch,
            'repository_create_date': item.created_at,
            'repository_update_date': item.updated_at,
        }
        # _logger.warning(vals)
        return vals






