# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
import os
from random import randint

_logger = logging.getLogger(__name__)


class CustomAddon(models.Model):
    _inherit = "custom.addon"

    @api.model
    def _prepare_dashboard_fields(self):
        return {
            "all_organizations": 0,
            "all_repositories": 0,
            "all_branches": 0,
            "all_addons": 0,
            "today_sync_organizations": 0,
            "today_sync_repositories": 0,
            "today_sync_branches": 0,
            "today_sync_addons": 0,
            "today_created_organization": 0,
            "today_created_repository": 0,
            "today_created_branches": 0,
            "today_created_addons": 0,
            "today_updated_addons": 0,
            "active_branches": 0,
            "my_addons": 0,
            "my_repositories": 0,
            "all_category": 0,
            "all_author": 0,
        }

    @api.model
    def retrieve_dashboard(self):
        """This function returns the values to populate the custom dashboard in
        the purchase order views.
        """
        self.check_access_rights("read")
        values = self._prepare_dashboard_fields()
        today = fields.Date.context_today(self)

        Organization = self.env["git.organization"]
        Repository = self.env["git.repository"]
        Branch = self.env["git.branch"]
        favorites_domain = [("favorite_user_ids", "in", self.env.user.id)]
        sync_domain = [("is_synchronized", "=", True)]
        create_today = [("create_date", ">=", today)]
        update_today = [("write_date", ">=", today)]
        sync_today = [("last_sync_date", ">=", today)]

        records = self.search([])
        branches = records.mapped("branch_ids")

        values.update(
            {
                "all_organizations": Organization.search_count([]),
                "all_repositories": Repository.search_count([]),
                "all_branches": Branch.search_count([]),
                "all_addons": len(records),
                "today_sync_organizations": Organization.search_count(sync_domain),
                "today_sync_repositories": Repository.search_count(sync_domain),
                "today_sync_branches": Branch.search_count(sync_domain),
                "today_sync_addons": int(
                    round(
                        len(records.filtered_domain(sync_today)) * 100 / len(records), 2
                    )
                )
                if records
                else 0,
                "today_created_organization": Organization.search_count(create_today),
                "today_created_repository": Repository.search_count(create_today),
                "today_created_branches": Branch.search_count(create_today),
                "today_created_addons": len(records.filtered_domain(create_today)),
                "today_updated_addons": len(records.filtered_domain(update_today)),
                "active_branches": len(branches),
                "my_addons": len(records.filtered_domain(favorites_domain)),
                "my_repositories": Repository.search_count(favorites_domain),
                "all_category": len(records.mapped("category_id")),
                "all_author": len(list(set(records.mapped("author")))),
            }
        )

        return values
