# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import tools
from odoo import api, fields, models


class SaleReport(models.Model):
    _name = "custom.addon.report"
    _description = "Custom Addons Analysis Report"
    _auto = False
    _rec_name = 'date'
    _order = 'date desc'

    @api.model
    def _get_done_states(self):
        return ['sale', 'done', 'paid']

    name = fields.Char('Name', readonly=True)
    category_id = fields.Many2one('ir.module.category', 'Category', readonly=True)

    custom_addon_id = fields.Many2one('custom.addon', 'Custom Addon', readonly=True)

    def _select_sale(self, fields=None):
        if not fields:
            fields = {}
        select_ = """
            coalesce(min(l.id), -s.id) as id,
            s.name as name,
            s.category_id as category_id,
            s.id as custom_addon_id
        """

        for field in fields.values():
            select_ += field
        return select_

    def _from_sale(self, from_clause=''):
        from_ = """
                %s
        """ % from_clause
        return from_

    def _group_by_sale(self, groupby=''):
        groupby_ = """
            s.category_id,
            s.id %s
        """ % (groupby)
        return groupby_

    def _query(self, with_clause='', fields=None, groupby='', from_clause=''):
        if not fields:
            fields = {}
        with_ = ("WITH %s" % with_clause) if with_clause else ""
        return '%s (SELECT %s FROM %s WHERE l.display_type IS NULL GROUP BY %s)' % \
               (with_, self._select_sale(fields), self._from_sale(from_clause), self._group_by_sale(groupby))

    def init(self):
        # self._table = sale_report
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""CREATE or REPLACE VIEW %s as (%s)""" % (self._table, self._query()))

