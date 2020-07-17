# -*- coding: utf-8 -*-
# Copyright (C) DEC SARL, Inc - All Rights Reserved.
# Written by Yann Papouin <y.papouin at dec-industrie.com>, Mar 2020

from odoo import api, fields, models


class RefProduct(models.Model):
    _inherit = "product.product"

    ciel_code = fields.Char('Ciel', size=24)
    comments = fields.Text('Comments')
    market_bom_id = fields.Many2one(
        'ref.market.bom',
        'Market bill of materials and services',
    )
    market_markup_rate = fields.Float(
        'Markup rate',
        help='Used by REF manager Market',
    )
    market_material_cost_factor = fields.Float(
        'Material factor (PF)',
        help='Used by REF manager Market',
    )

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []
        if not name:
            return None
        # Make a search with default criteria
        result = super().name_search(
            name=name, args=args, operator=operator, limit=limit
        )

        # Make a specific search according to market reference
        products = self.search(
            [
                ('ciel_code', '=', name), '|', ('state', '!=', 'obsolete'),
                ('state', '=', False)
            ],
            limit=limit
        )
        if products:
            res2 = []
            ciel_result = products.name_get()
            for item in ciel_result:
                item = list(item)
                item[1] = ('%s (%s)') % (item[1], name)
                res2.append(item)
            result = res2 + result

        # Make a specific search to find a product with version inside
        if not result and 'V' in name.upper():
            reference = name.upper().rpartition('V')
            if reference[0]:
                res = []
                products = self.search(
                    [('default_code', 'ilike', reference[0])], limit=limit
                )
                res = products.name_get()
                result = res + result
        """
        # Search for obsolete products
        ids = [item[0] for item in result] 
        ids = self.search(cr, user, [('state', '=', 'obsolete'), ('id', 'in', ids)], limit=limit, context=context)
        if ids:
            for i, item in enumerate(result):
                if item[0] in ids: 
                    item = list(item)
                    item[1] = ('%s (OBSOLETE)') % (item[1])
                    result[i] = tuple(item) 
        """

        return result


# class ref_task_wizard(models.Model_memory):
#     _name = 'ref.task.wizard'

#     def action_start_task(self, cr, uid, data, context):
#         ref_reference_obj = self.pool.get('ref.reference')
#         ref_price_obj = self.pool.get('ref.price')

#         #ref_reference_obj.run_material_cost_scheduler(cr, uid)

#         # Remove duplicates
#         ids = ref_reference_obj.search(cr, uid, [], context=context)

#         for reference in ref_reference_obj.browse(cr, uid, ids, context=context):
#             price_ids = ref_price_obj.search(cr, uid, [('reference_id','=', reference.id)], context=context, order='date asc')
#             if price_ids:
#                 price_ids_to_delete = []
#                 previous_price = False
#                 for i, price in enumerate(ref_price_obj.browse(cr, uid, price_ids, context=context)):
#                     assert(price_ids[i] == price.id)
#                     if previous_price and price.value == previous_price.value:
#                         #print 'Add %s to delete' % (price.date)
#                         price_ids_to_delete.append(price.id)
#                     previous_price = price

#                 if price_ids_to_delete:
#                     assert(len(price_ids_to_delete)<ids)
#                     diff = [x for x in price_ids if x not in price_ids_to_delete]
#                     ref_price_obj.unlink(cr, uid, price_ids_to_delete, context=context)
#                     logging.getLogger('ref.task.wizard').info('Remaining ids %s for [%s] %s', diff, reference.value, reference.product.name)

#         today = time.strftime('%Y-%m-%d')
#         ref_reference_obj.generate_material_cost_report(cr, uid, ids, '2014-01-01', today, context=context)
#         #ref_reference_obj.generate_material_cost_report(cr, uid, ids, False, False, context=context)

#         #ref_reference_obj.run_material_cost_scheduler(cr, uid, context=context)

#         return {}

# ref_task_wizard()
