# -*- coding: utf-8 -*-

from multiprocessing import synchronize
from odoo import models, fields, api

import logging
from random import randint

_logger = logging.getLogger(__name__)


class GitRules(models.Model):
    _name = "git.rules"
    _description = "Git Rules"
    _inherits = {'base.automation': 'automation_id'}
    _check_company_auto = True

    automation_id = fields.Many2one('base.automation', 'Automated Action', required=True, ondelete='restrict')

