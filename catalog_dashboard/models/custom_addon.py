# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
import os
from random import randint

_logger = logging.getLogger(__name__)


class CustomAddon(models.Model):
    _inherit = 'custom.addon'

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        self.check_access_rights('read')
        today = fields.Date.context_today(self)
        Organization = self.env['git.organization']
        Repository = self.env['git.repository']
        Branch = self.env['git.branch']
        favorites_domain = [('favorite_user_ids', 'in', self.env.user.id)]
        sync_domain = [('is_synchronized', '=', True)]
        create_today = [('create_date', '>=', today)]
        update_today = [('write_date', '>=', today)]
        sync_today = [('last_sync_date', '>=', today)]

        records = self.search([])
        branches = records.mapped('branch_ids')



        result = {
            'all_organization': Organization.search_count([]),
            'all_repository': Repository.search_count([]),
            'all_branches': Branch.search_count([]),
            'sync_organization': Organization.search_count(sync_domain),
            'sync_repository': Repository.search_count(sync_domain),
            'sync_branches': Branch.search_count(sync_domain),
            'create_organization': Organization.search_count(create_today),
            'create_repository': Repository.search_count(create_today),
            'create_branches': Branch.search_count(create_today),
            'all_addons': len(records),
            'active_branches': len(branches),
            'my_addons': len(records.filtered_domain(favorites_domain)),
            'my_repositories': Repository.search_count(favorites_domain),
            'create_addons': len(records.filtered_domain(create_today)),
            'update_addons': len(records.filtered_domain(update_today)),
            'today_sync_addons': round(len(records.filtered_domain(sync_today)) * 100 / len(records), 2),
            'all_category': len(records.mapped('category_id')),
            'all_author': len(list(set(records.mapped('author')))),
        }

        _logger.error(result)

        # result = {
        #     'all_to_send': 0,
        #     'all_waiting': 0,
        #     'all_late': 0,
        #     'my_to_send': 0,
        #     'my_waiting': 0,
        #     'my_late': 0,
        #     'all_avg_order_value': 0,
        #     'all_avg_days_to_purchase': 0,
        #     'all_total_last_7_days': 0,
        #     'all_sent_rfqs': 0,
        #     'company_currency_symbol': self.env.company.currency_id.symbol
        # }

        # return result

        return result