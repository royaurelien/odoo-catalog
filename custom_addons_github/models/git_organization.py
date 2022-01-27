# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api
from odoo.tools import datetime

from datetime import datetime
from github import Github
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
        return Github(self.token)

    def _get_items_from_github(self):
        self.ensure_one()
        g = self._get_github()
        org = g.get_organization(self.name)
        return org.get_repos()

    def _convert_github_to_odoo(self, item):
        vals = {
            'organization_id': self.id,
            'repo_id': item.id,
            'name': item.full_name,
            'path': item.name,
            'description': item.description,
            'url': item.url,
            'http_git_url' : item.clone_url,
            'ssh_git_url' : item.git_url,
            # 'repository_create_date': self._gitlab_date_to_datetime(project.created_at),
            # 'repository_update_date': self._gitlab_date_to_datetime(project.last_activity_at),
        }
        # _logger.warning(vals)
        return vals






