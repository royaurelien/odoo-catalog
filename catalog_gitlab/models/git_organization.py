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
TYPE = [('gitlab', 'Gitlab')]

_logger = logging.getLogger(__name__)

class GitOrganization(models.Model):
    _inherit = 'git.organization'

    service = fields.Selection(selection_add=TYPE)
    option_keep_base_url = fields.Boolean(default=False)
    option_limit_visibility = fields.Boolean(default=False)
    option_visibility = fields.Selection([('public', 'Public'), ('internal', 'Internal'), ('private', 'Private')], string="Visibility")


    def _get_namespaces_from_gitlab(self):
        self.ensure_one()
        gl = self._get_gitlab()
        return [{'name': item.name, 'namespace_id':item.id} for item in gl.groups.list()]


    def _create_repository_from_gitlab(self, vals):
        self.ensure_one()
        gl = self._get_gitlab()

        branch_name = vals.get('branch_name', False)
        keys = ['name', 'description', 'visibility', 'namespace_id', 'path']

        values = {k:v for k,v in vals.items() if k in keys}

        if branch_name:
            values.update({
                'initialize_with_readme': True,
                'default_branch': branch_name,
            })

        _logger.warning(values)

        try:
            project = gl.projects.create(values)
        except gitlab.GitlabCreateError as error:
            _logger.warning(error)
            project = False

        _logger.warning(project)

        if project:
            repository_vals = self._convert_gitlab_to_odoo(project)
            _logger.error(repository_vals)
            repository = self.env['git.repository'].create(repository_vals)
            
            return repository
            # return False
            # self.write({'repository_ids': [(0, False, self._convert_gitlab_to_odoo(project))]})

        return True


    def _get_gitlab(self):
        self.ensure_one()
        return gitlab.Gitlab(url=self.url, private_token=self.auth_id.token)
        # return gitlab.Gitlab(url=self.url, private_token=self.auth_id.token, keep_base_url=True)


    def _get_items_from_gitlab(self, **kwargs):
        self.ensure_one()
        gl = self._get_gitlab()
        _logger.error(gl)
        projects = gl.projects.list(visibility='private')
        # projects = gl.projects.list(all=True, order_by='last_activity_at')[:2]
        _logger.error(projects)
        res = [repo for repo in projects]

        return res


    def _gitlab_date_to_datetime(self, curr_date):
        # ISO8601
        # 2022-01-20T10:36:21.680
        return datetime.fromisoformat(curr_date.replace('Z', '+00:00')).replace(tzinfo=None)


    def _convert_gitlab_to_odoo(self, item, **kwargs):

        search_contributors = kwargs.get('contributors', False)

        vals = {
            'organization_id': self.id,
            'repo_id': item.id,
            'name': item.name,
            'path': item.path,
            'description': item.description,
            'url': item.web_url,
            'http_git_url' : item.http_url_to_repo,
            'ssh_git_url' : item.ssh_url_to_repo,
            'repository_create_date': self._gitlab_date_to_datetime(item.created_at),
            'repository_update_date': self._gitlab_date_to_datetime(item.last_activity_at),
        }

        if search_contributors:
            contributors = item.repository_contributors()
            Contributors = self.env['git.contributor']
            vals_list = []

            for contributor in contributors:
                name = contributor.get('name')
                email = contributor.get('email')
                record = Contributors.search([('name', '=', name), ('email', '=', email)], limit=1)

                vals_list.append((0, False, {'name': name, 'email': email}) if not record else (4, record.id, False))

            _logger.warning(vals_list)
            vals['contributor_ids'] = vals_list

        return vals






