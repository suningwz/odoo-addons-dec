# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

import time
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ref_market_category(models.Model):
    """ Description """

    _name = 'ref.market.category'
    _description = 'Market Category'
    _rec_name = 'description'
    _order = 'sequence'

    prefix = fields.Char('Prefix', size=6, required=True)
    description = fields.Char('Description', size=128, required=True)
    sequence = fields.Integer('Position', required=True)

