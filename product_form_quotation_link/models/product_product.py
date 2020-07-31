# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Jul 2020

from datetime import timedelta

from odoo import api, fields, models, _
from odoo.tools.float_utils import float_round


class ProductProduct(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    in_quotation_product_qty = fields.Float(
        compute='_compute_in_quotation_product_qty',
        string='In Quotation',
    )

    @api.multi
    def _compute_in_quotation_product_qty(self):
        date_from = fields.Datetime.to_string(
            fields.datetime.now() - timedelta(days=365)
        )
        domain = [
            ('state', 'in', ['draft', 'sent', 'to approve']),
            ('product_id', 'in', self.mapped('id')),
            ('date_order', '>', date_from)
        ]
        order_lines = self.env['purchase.order.line'].read_group(
            domain, ['product_id', 'product_uom_qty'], ['product_id']
        )
        purchased_data = dict(
            [
                (data['product_id'][0], data['product_uom_qty'])
                for data in order_lines
            ]
        )
        for product in self:
            product.in_quotation_product_qty = float_round(
                purchased_data.get(product.id, 0),
                precision_rounding=product.uom_id.rounding
            )