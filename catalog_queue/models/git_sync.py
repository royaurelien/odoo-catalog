# -*- coding: utf-8 -*-

from collections import ChainMap, OrderedDict
import logging
# from multiprocessing import synchronize

from odoo import models, fields, api, _
from odoo.addons.queue_job.delay import group, chain



_logger = logging.getLogger(__name__)


class GitSync(models.AbstractModel):
    _inherit = "git.sync"


    def _get_batch_name(self):
        # ", ".join(list(map(str, self.ids)))
        return f"{self._description}: {self.ids[0]}..{self.ids[-1]} ({len(self.ids)})"


    @api.model
    def action_sync_with_delay(self, ids=[], **kwargs):

        values = self._prepare_sync_values(kwargs)
        result = []
        # values['cron_mode'] = True
        all_records = self.browse(ids)
        # batch = self.env['queue.job.batch'].get_new_batch(all_records._get_batch_name())
        batch = self.env['queue.job.batch'].get_new_batch(self._description)
        chunk_ids = all_records._group_records_by_identidier(values)

        message = f"Synchronizing {self._description}: {chunk_ids[0]}..{chunk_ids[-1]} ({len(chunk_ids)})"
        self.env.user.notify_info(message=message)

        # group_a = group(*[self.delayable()._action_sync(current_ids, cron=False) for current_ids in chunk_ids])
        # chain(group_a).delay()



        # return True

        for current_ids in chunk_ids:
            # records = all_records.browse(current_ids)


            message = f"Synchronizing {self._description}: {len(current_ids)} item(s)"
            # res = self.with_context(job_batch=batch).with_delay(channel='catalog')._action_sync(current_ids, **values)
            # self.with_delay()._action_sync(current_ids, **values)
            self.with_context(job_batch=batch).with_delay(channel='catalog')._action_sync(current_ids, cron=False)
            # self._action_sync(current_ids, **values)
            self.env.user.notify_info(message=message)

            # for record in records:

            #     _logger.warning(record)

            #     # # message = f"Synchronizing {self._description}: {current_ids[0]}..{current_ids[-1]} ({len(current_ids)})"
            #     message = f"Synchronizing {self._description}: {record.id} ({len(record)})"

            #     self = record.with_context(job_batch=batch)
            #     self.with_context(job_batch=batch).with_delay(channel='catalog')._action_process(**values)
            #     self.env.user.notify_info(message=message)

            #     # res = record._action_process(**values)
            #     # result.append(res)

        batch.enqueue()
        return True

