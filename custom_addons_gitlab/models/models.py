# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api
from odoo.tools import datetime

from datetime import datetime
import gitlab
import logging
import re
import os

REGEX_MAJOR_VERSION = re.compile("^(0|[1-9]\d*)\.(0|[1-9]\d*)$")
TYPE = [('gitlab', 'GitLab')]

_logger = logging.getLogger(__name__)

class GitOrganization(models.Model):
    _inherit = 'git.organization'

    service = fields.Selection(selection_add=TYPE)

    def _get_gitlab(self):
        self.ensure_one()
        return gitlab.Gitlab(url=self.url, private_token=self.token)

    def _get_from_gitlab(self, **kwargs):
        gl = self._get_gitlab()
        projects = gl.projects.list(**kwargs)

        # _logger.warning(projects)

        res = [self._prepare_gitlab_to_odoo(project) for project in projects]
        return res

    def _gitlab_date_to_datetime(self, curr_date):
        # ISO8601
        # 2022-01-20T10:36:21.680
        return datetime.fromisoformat(curr_date.replace('Z', '+00:00')).replace(tzinfo=None)

    def _prepare_gitlab_to_odoo(self, project):
        vals = {
            'organization_id': self.id,
            'repo_id': project.id,
            'name': project.name,
            'path': project.path,
            'description': project.description,
            'url': project.web_url,
            'http_git_url' : project.http_url_to_repo,
            'ssh_git_url' : project.ssh_url_to_repo,
            'repository_create_date': self._gitlab_date_to_datetime(project.created_at),
            'repository_update_date': self._gitlab_date_to_datetime(project.last_activity_at),
        }
        # _logger.warning(vals)
        return vals


    def _action_sync_repository(self):
        for record in self.filtered(lambda x: x.service == 'gitlab'):
            projects = record._get_from_gitlab() # all=True
            repo_ids = {e['repo_id']:e['id'] for e in record.repository_ids.read(['repo_id'])}

            to_update = [(1, repo_ids.get(vals['repo_id']), vals) for vals in projects if vals['repo_id'] in repo_ids.keys()]
            to_create = [(0, False, vals) for vals in projects if vals['repo_id'] not in repo_ids]

            _logger.warning("[{}] {} Repositories found (updated: {}, created: {})".format(record.name, len(projects), len(to_update), len(to_create)))
            record.update({'repository_ids': to_update + to_create})

            record.repository_ids._action_sync_branches()



class GitRepository(models.Model):
    _inherit = 'git.repository'

    def _get_from_gitlab(self, **kwargs):
        gl = self.organization_id._get_gitlab()
        project = gl.projects.get(self.repo_id)
        branches = project.branches.list()

        return [self._convert_gitlab_to_odoo(branch) for branch in branches]

    def _convert_gitlab_to_odoo(self, branch):
        vals = {
            'repository_id': self.id,
            'name': branch.name,
            'major': bool(REGEX_MAJOR_VERSION.match(branch.name)),
            'url': branch.web_url,
        }

        if branch.commit:
            vals.update({
                'last_commit_message': branch.commit.get('title'),
                'last_commit_author': branch.commit.get('author_email'),
                'last_commit_short_id': branch.commit.get('short_id'),
                'last_commit_url': branch.commit.get('web_url'),
            })

        _logger.warning(vals)
        return vals

    def _action_sync_branches(self):
        for record in self:
            branches = record._get_from_gitlab()

            branch_ids = {e['name']:e['id'] for e in record.branch_ids.read(['name'])}

            to_update = [(1, branch_ids.get(vals['name']), vals) for vals in branches if vals['name'] in branch_ids.keys()]
            to_create = [(0, False, vals) for vals in branches if vals['name'] not in branch_ids]

            _logger.warning("[{}] {} Branches found (updated: {}, created: {})".format(record.name, len(branches), len(to_update), len(to_create)))
            record.update({'branch_ids': to_update + to_create})


class GitBranch(models.Model):
    _inherit = 'git.branch'

    def _get_from_gitlab(self, **kwargs):
        gl = self.repository_id.organization_id._get_gitlab()
        project = gl.projects.get(self.repository_id.repo_id)

        _logger.warning(project.name)

        requirements = False
        addons = []

        items = project.repository_tree(ref=self.name)
        for item in items:
            if item['name'] == 'requirements.txt':
                # f = project.files.get(file_path=item['path'], ref=self.name)
                # requirements = f.decode()
                requirements = True

            elif item['type'] == 'tree':
                for name in ['__manifest__.py', '__openerp__.py']:
                    try:
                        f = project.files.get(file_path=os.path.join(item['path'], name), ref=self.name)
                        manifest = eval(f.decode())
                        addons.append((item['path'], manifest))
                        break

                    except gitlab.GitlabGetError:
                        continue

        addons = [self._convert_gitlab_to_odoo(addon[0], addon[1]) for addon in addons]
        return addons, requirements



    def _convert_gitlab_to_odoo(self, dir_name, manifest):
        vals = {
            'name': manifest.get('name'),
            'technical_name': dir_name,
            'version': manifest.get('version'),
            # 'branch_ids': [(0, False, )]
        }

        _logger.warning(vals)
        return vals

    def _action_sync_addons(self):
        for record in self:
            (addons, requirements) = record._get_from_gitlab()

            # branch_ids = {e['name']:e['id'] for e in record.branch_ids.read(['name'])}

            # to_update = [(1, branch_ids.get(vals['name']), vals) for vals in branches if vals['name'] in branch_ids.keys()]
            # to_create = [(0, False, vals) for vals in branches if vals['name'] not in branch_ids]

            # _logger.warning("[{}] {} Branches found (updated: {}, created: {})".format(record.name, len(branches), len(to_update), len(to_create)))
            # record.update({'branch_ids': to_update + to_create})