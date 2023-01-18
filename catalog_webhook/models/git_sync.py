# -*- coding: utf-8 -*-


import logging

from odoo import models, fields, api, registry, _

_logger = logging.getLogger(__name__)


class GitSync(models.AbstractModel):
    _inherit = "git.sync"


    def _convert_webhook_to_odoo(self, data, **kwargs):
        return self.__get_method("_convert_{}_webhook_to_odoo", self.service, {}, data, **kwargs)