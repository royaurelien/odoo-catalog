# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class AbstractGitModel(models.AbstractModel):
    _name = "abstract.git.model"
    _description = "Git abstract model"

    # _github_type = "repository"

    _git_service = "repository_id.service"
    _git_field_rel = 'repository_id'
    _git_field_name = 'repo_id'

    last_sync_date = fields.Datetime(string="Last Sync Date", readonly=True)
    service = fields.Selection([])


    def _get_service(self, name):
        pass

    def __get_method(self, name, value, default_value, *args, **kwargs):
        method = name.format(value)
        found = hasattr(self, method)
        _logger.warning("Search {} in {}: {}".format(method, self._name, found))
        return getattr(self, method)(*args) if hasattr(self, method) else default_value

    def _convert_to_odoo(self, item):
        return self.__get_method("_convert_{}_to_odoo", self.service, {}, item)

    def _get_items_for_odoo(self, service=None):
        return self.__get_method("_get_items_from_{}", self.service, {})


    @api.model
    def _action_sync(self, ids):
        records = self.browse(ids)

        # if not self._git_service:
        #     raise ""

        for service_name in list(set(records.mapped(self._git_service))):
            # service = self._get_service()
            service = None

            _logger.error(service_name)

            records_by_service = records.filtered(lambda rec: rec.service == service_name)

            _logger.error(records_by_service)

            for record in records_by_service:
                _logger.warning(record)
                # get items
                items = record._get_items_for_odoo()
                _logger.error(items)

                # prepare values
                vals_list = [record._convert_to_odoo(item) for item in items]
                match_field = record._git_field_name
                rel_field = record._git_field_rel
                model_name = record[rel_field]._name

                object_ids = {e[match_field]:e['id'] for e in record[rel_field].read([match_field])}

                to_update = [(1, object_ids.get(vals[match_field]), vals) for vals in vals_list if vals[match_field] in object_ids.keys()]
                to_create = [(0, False, vals) for vals in vals_list if vals[match_field] not in object_ids]

                # TODO: Search & apply rules before update

                _logger.warning("{} '{}' >> {} {} found (updated: {}, created: {})".format(self._name,
                                                                                     record.name,
                                                                                     len(vals_list),
                                                                                     model_name,
                                                                                     len(to_update),
                                                                                     len(to_create)))
                record.update({rel_field: to_update + to_create})

            # if method:
            #     _logger.warning('Call {} for {}'.format(method_name, len(records_by_service)))
            #     method()


    def action_sync(self):
        self._action_sync(self.ids)