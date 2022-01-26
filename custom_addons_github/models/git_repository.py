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

class GitRepository(models.Model):
    _inherit = 'git.repository'



    def _get_github(self):
        self.ensure_one()
        return Github(self.token)

    def _get_from_github(self, **kwargs):
        g = self._get_github()
        org = g.get_organization(self.name)
        repos = org.get_repos()

        # _logger.warning(projects)

        return [self._prepare_github_to_odoo(repo) for repo in repos]

    def _github_date_to_datetime(self, curr_date):
        # ISO8601
        # 2022-01-20T10:36:21.680
        return datetime.fromisoformat(curr_date.replace('Z', '+00:00')).replace(tzinfo=None)

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


    def _action_sync_repository_github(self):
        for record in self.filtered(lambda x: x.service == TYPE[0][0]):
            projects = record._get_from_github()
            repo_ids = {e['repo_id']:e['id'] for e in record.repository_ids.read(['repo_id'])}

            to_update = [(1, repo_ids.get(vals['repo_id']), vals) for vals in projects if vals['repo_id'] in repo_ids.keys()]
            to_create = [(0, False, vals) for vals in projects if vals['repo_id'] not in repo_ids]

            _logger.warning("[{}] {} Repositories found (updated: {}, created: {})".format(record.name, len(projects), len(to_update), len(to_create)))
            record.update({'repository_ids': to_update + to_create})




