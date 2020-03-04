# Copyright (C) DEC SARL, Inc - All Rights Reserved.
#
# CONFIDENTIAL NOTICE: Unauthorized copying and/or use of this file,
# via any medium is strictly prohibited.
# All information contained herein is, and remains the property of
# DEC SARL and its suppliers, if any.
# The intellectual and technical concepts contained herein are
# proprietary to DEC SARL and its suppliers and may be covered by
# French Law and Foreign Patents, patents in process, and are
# protected by trade secret or copyright law.
# Dissemination of this information or reproduction of this material
# is strictly forbidden unless prior written permission is obtained
# from DEC SARL.
# Written by Yann Papouin <y.papouin@dec-industrie.com>, Mar 2020

import time
import logging

from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class ref_reference(models.Model):
    """ Description """

    _name = 'ref.reference'
    _description = 'Reference'
    _rec_name = 'value'
    _order = 'value'

    category = fields.Many2one(
        'ref.category',
        'Category',
        required=True,
    )
    product = fields.Many2one(
        'product.product',
        'Product',
        required=True,
    )
    product_ciel_code = fields.Char(
        related='product.ciel_code',
        string='Ciel',
    )
    product_name = fields.Char(
        related='product.name',
        string='Name',
    )
    product_state = fields.Selection(
        related='product.state',
        string='Status',
    )
    product_comments = fields.Text(
        related='product.comments',
        string='Comments',
    )
    current_version = fields.Integer(
        'Current version',
        required=True,
    )
    value = fields.Text(
        'Value',
        required=True,
    )
    searchvalue = fields.Text(
        'Search value',
        required=True,
    )
    datetime = fields.Datetime(
        'Create date', required=True, default=fields.Datetime.now
    )
    folder_count = fields.Integer('Product folder item count')
    folder_error = fields.Integer('Product folder error count')
    folder_warning = fields.Integer('Product folder warning count')
    folder_task = fields.Integer('Product folder task count')
    picturepath = fields.Text('Path to picture')

    reference_lines = fields.One2many('ref.reference.line', 'reference')
    version_lines = fields.One2many('ref.version', 'reference')
    price_lines = fields.One2many('ref.price', 'reference_id')

    _sql_constraints = [
        ('value_uniq', 'unique(value)', 'Reference value must be unique !'),
    ]

    @api.model
    def search_custom(self, keywords):
        res = []
        for key in keywords[0]:
            if key and key[0] == '+':
                use_comments = True
                key = key[1:]
            else:
                use_comments = False

            if key:
                search_value = self.search([('searchvalue', 'ilike', key)])
                search_category = self.search([('category.name', 'ilike', key)])
                search_name = self.search([('product.name', 'ilike', key)])
                search_ciel = self.search([('product.ciel_code', '=', key)])

                if use_comments:
                    search_comments = self.search(
                        [('product.comments', 'ilike', key)]
                    )
                else:
                    search_comments = []

                if len(key) > 2:
                    search_tags = self.search(
                        [('product.tagging_ids.name', 'ilike', key)]
                    )
                else:
                    search_tags = []

                res = res + search_value + search_category + search_name + search_comments + search_ciel + search_tags

        return res

    @api.multi
    def run_material_cost_scheduler(self):
        mrp_bom_obj = self.env['mrp.bom']
        ref_price_obj = self.env['ref.price']

        ids = self.ids
        if not self.ids:
            ids = self.search([])
        for reference in self.browse(ids):
            if reference.category.code in ['ADT']:
                continue
            #_logger.info("Reference category name is {0}".format(reference.category.name))
            data = {}
            cost_price = 0.0
            if reference.product and reference.product.bom_ids:
                bom_id = mrp_bom_obj._bom_find(product=reference.product)
                if bom_id:
                    _logger.info(
                        'Compute material cost price for [%s] %s',
                        reference.value, reference.product.name
                    )
                    try:
                        cost_price = mrp_bom_obj.get_cost_price([bom_id]
                                                               )[bom_id]
                    except Exception as e:
                        _logger.exception(
                            "Failed to get cost price for [%s] %s\n %s",
                            reference.value, reference.product.name, e
                        )

            ref_price = False
            ref_price_ids = ref_price_obj.search(
                [('reference_id', '=', reference.id)], limit=1
            )
            if ref_price_ids:
                ref_price = ref_price_obj.browse(ref_price_ids)[0]

            if not ref_price or (
                round(ref_price.value, 2) != round(cost_price, 2)
            ):
                #abs(ref_price.value - cost_price) > 0.1
                data['reference_id'] = reference.id
                data['value'] = cost_price
                ref_price_obj.create(data)
            else:
                _logger.info(
                    'Price did not change for [%s] %s', reference.value,
                    reference.product.name
                )

        self.generate_material_cost_report(ids)

    @api.model
    def generate_material_cost_report(
        self, ids, date_ref1=False, date_ref2=False
    ):
        ref_price_obj = self.pool.get('ref.price')
        mail_message_obj = self.env['mail.mail'].sudo()

        if not ids:
            ids = self.search([])

        today = time.strftime('%Y-%m-%d')
        emailfrom = 'refmanager@dec-industrie.com'
        emails = ['decindustrie@gmail.com']
        subject = _('Price surcharge alert')
        body = ('%s\n\n') % (self.env.cr.dbname)
        ref_content = []

        for reference in self.browse(ids):
            if reference.category.name in ['ADT']:
                continue
            ref1_ids = []
            ref2_ids = []
            if date_ref1:
                ref1_ids = ref_price_obj.search(
                    [
                        ('reference_id', '=', reference.id),
                        ('date', '<=', date_ref1)
                    ],
                    limit=1
                )
            if date_ref2:
                ref2_ids = ref_price_obj.search(
                    [
                        ('reference_id', '=', reference.id),
                        ('date', '<=', date_ref2)
                    ],
                    limit=1
                )

            if ref1_ids and ref2_ids:
                price_ids = ref2_ids + ref1_ids
            else:
                price_ids = ref_price_obj.search(
                    [('reference_id', '=', reference.id)], limit=2
                )

            if (len(price_ids) >= 2):
                prices = ref_price_obj.browse(price_ids)
                if (round(prices[0].value, 2) > round(prices[1].value, 2)) and (
                    (date_ref1 or date_ref2) or (prices[0].date == today)
                ):
                    assert (prices[0].id == price_ids[0])
                    ref_content.append(
                        {
                            'id': reference.id,
                            'reference': reference.value,
                            'product': reference.product.name,
                            'price0_date': prices[0].date,
                            'price0_value': prices[0].value,
                            'price1_date': prices[1].date,
                            'price1_value': prices[1].value,
                            'diff': prices[0].value - prices[1].value
                        }
                    )

        ref_content = sorted(ref_content, key=lambda k: k['diff'], reverse=True)
        for content in ref_content:
            body += ('[%s] %s - %d\n') % (
                content['reference'], content['product'], content['id']
            )
            body += ('%s:   %.2f\n'
                    ) % (content['price1_date'], content['price1_value'])
            body += ('%s:   %.2f (+%.2f)\n') % (
                content['price0_date'], content['price0_value'],
                content['price0_value'] - content['price1_value']
            )
            body += '\n'

        if ref_content:
            mail_message_obj.create(
                {
                    #'email_from': emailfrom,
                    'email_to': emails,
                    'subject': subject,
                    'body_html': body
                }
            )