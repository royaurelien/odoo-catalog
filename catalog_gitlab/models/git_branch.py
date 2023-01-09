# -*- coding: utf-8 -*-

import gitlab
import logging
import os

from odoo import models, fields, api

MANIFEST_NAMES = ['__manifest__.py', '__openerp__.py']


_logger = logging.getLogger(__name__)

class GitBranch(models.Model):
    _inherit = 'git.branch'

    def _get_items_from_gitlab(self):
        self.ensure_one()

        gl = self.repository_id.organization_id._get_gitlab()
        project = gl.projects.get(self.repository_id.repo_id)

        test, limit = self._get_test_mode()
        count = 0
        requirements = False
        addons = []
        python_modules = []

        items = project.repository_tree(ref=self.name, get_all=True)
        for item in items:
            if item['name'] == 'requirements.txt':
                f = project.files.get(file_path=item['path'], ref=self.name)
                python_modules = f.decode().splitlines()
                python_modules = ", ".join([e.decode() for e in python_modules]) if python_modules else ""
                requirements = True

            elif item['type'] == 'tree':
                for filename in MANIFEST_NAMES:
                    try:
                        f = project.files.get(file_path=os.path.join(item['path'], filename), ref=self.name)
                        manifest = eval(f.decode())
                        manifest['technical_name'] = item['path']

                        try:
                            index_html = 'static/description/index.html'
                            f = project.files.get(file_path=os.path.join(item['path'], index_html), ref=self.name)
                            web_description = f.decode()
                            manifest['web_description'] = web_description

                        except gitlab.GitlabGetError:
                            pass

                        addons.append(manifest)
                        break
                    except gitlab.GitlabGetError:
                        continue
            count += 1

            if test and count >= limit:
                break

        vals = {
            'requirements': requirements,
            'python_modules': python_modules,
        }
        self.update(vals)

        return addons


    def _convert_gitlab_to_odoo(self, item):
        self.ensure_one()

        mapping, keys = self._get_manifest_mapping()
        vals = {k:item.get(v, False) for k,v in mapping.items()}

        return vals


