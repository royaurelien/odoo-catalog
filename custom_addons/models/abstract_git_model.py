# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class AbstractGitModel(models.AbstractModel):
    _name = "abstract.git.model"
    _description = "Git abstract model"

    _github_type = "repository"
    _git_service = "repository_id.service"

    _git_field_rel = 'repository_id'
    _git_field_name = 'repo_id'

    last_sync_date = fields.Datetime(string="Last Sync Date", readonly=True)
    service = fields.Selection([])

    #######################

    def _get_gitlab(self):
        self.ensure_one()
        return gitlab.Gitlab(url=self.url, private_token=self.token)

    def _get_from_gitlab(self, **kwargs):
        gl = self._get_gitlab()
        projects = gl.projects.list(**kwargs)

        # _logger.warning(projects)

        res = [self._prepare_gitlab_to_odoo(project) for project in projects]
        return res

    #######################

    def _get_service(self, name):
        pass

    def __get_method(self, name, value, default_value, *args, **kwargs):
        method = name.format(value)
        return getattr(self, method)(*args, **kwargs) if hasattr(self, method) else default_value

    def _convert_to_odoo(self, item):
        return self.__get_method("_convert_{}_to_odoo", self.service, {})
        # method_name = "_convert_{}_to_odoo".format(self.service)
        # return getattr(self, method_name)() if hasattr(self, method_name) else {}

    def _get_items_for_odoo(self, service):
        return self.__get_method("_get_items_from_", self.service, {}, service)
        # method_name = "_get_items_from_{}".format(self.service)
        # return getattr(self, method_name)(service) if hasattr(self, method_name) else []

    @api.model
    def _action_sync(self, ids):
        records = self.browse(ids)

        if not self._git_service:
            raise ""

        for service_name in list(set(records.mapped(self._git_service))):
            service = self._get_service()
            records_by_service = records.filtered(lambda rec: rec.service == service_name)

            method_name = "_action_sync_{}".format(service_name)
            method = getattr(records_by_service, method_name) if hasattr(records_by_service, method_name) else False

            for record in records_by_service:

                # get items
                items = record._get_items_for_odoo(service=service)



                # prepare values
                vals_list = [self._convert_to_odoo(item) for item in items]
                match_field = record._git_field_name
                rel_field = record._git_field_rel

                object_ids = {e[match_field]:e['id'] for e in record[rel_field].read([match_field])}

                to_update = [(1, object_ids.get(vals[self._git_field_name]), vals) for vals in vals_list if vals[match_field] in object_ids.keys()]
                to_create = [(0, False, vals) for vals in vals_list if vals[match_field] not in object_ids]

                _logger.warning("[{}] {} xxx found (updated: {}, created: {})".format(record.name, len(vals_list), len(to_update), len(to_create)))
                record.update({rel_field: to_update + to_create})

            # if method:
            #     _logger.warning('Call {} for {}'.format(method_name, len(records_by_service)))
            #     method()


    def action_sync(self):
        self._action_sync(self.ids)