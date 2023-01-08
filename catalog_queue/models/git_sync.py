# -*- coding: utf-8 -*-

from collections import ChainMap, OrderedDict
from datetime import datetime
import logging
from random import randint
import re
from multiprocessing import synchronize

from odoo import models, fields, api, _
from odoo.tools import safe_eval
from odoo.tools.misc import get_lang


_logger = logging.getLogger(__name__)


class GitSync(models.AbstractModel):
    _inherit = "git.sync"


    def _get_batch_name(self):
        return "Sync {}: {}".format(self._description, ", ".join(list(map(str, self.ids))))


    @api.model
    def action_sync_with_delay(self, ids=[], **kwargs):
        cron_mode = kwargs.get('cron', False)
        job_count = kwargs.get('job_count', 10)
        force_update = kwargs.get('force_update', False)
        sync_delay = kwargs.get('delay', self._get_sync_delay())
        # auto_search = kwargs.get('auto_search', False)

        self = self.browse(ids)
        batch = self.env['queue.job.batch'].get_new_batch(self._get_batch_name())

        records_by_service = [self.filtered(lambda rec: rec.service == service) for service in list(set(self.mapped('service')))]

        for records in records_by_service:
            prev_count = len(records)
            # records = records._filter_on_delay(sync_delay)
            _logger.warning("Filter items on delay: {}/{}".format(len(records), prev_count))


            chunked_ids = [records.ids[i:i+job_count] for i in range(0, len(records.ids), job_count)]
            for current_ids in chunked_ids:
                _logger.error(current_ids)
                names = records.filtered_domain([('id', 'in', current_ids)]).mapped('name')
                # self.with_delay()._action_sync(current_ids, cron=False, delay=sync_delay)
                # self.env['git.queue'].add('action_sync', self._name, current_ids)
                message = f"Synchronizing: {', '.join(names)} ({len(current_ids)})"
                self.env.user.notify_info(message=message)
                _logger.warning(message)
                self.with_context(job_batch=batch).with_delay(channel='catalog')._action_sync(current_ids, cron=False)

        batch.enqueue()