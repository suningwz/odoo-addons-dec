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

import math
import simplejson
import logging
from osv import fields,osv
from tools.translate import _

class product_pack_sale( osv.osv ):
    _name = 'product.pack.saleline'
    _rec_name = 'product_id'
    _columns = {
        'parent_product_id': fields.many2one('product.product', 'Parent Product', ondelete='cascade', required=True),
        'quantity': fields.float('Quantity', required=True ),
        'product_id': fields.many2one('product.product', 'Product', required=True ),
        'product_name': fields.related('product_id', 'name', type='char', string='Name'),
        'product_code': fields.related('product_id', 'default_code', type='char', string='Default code'),        
        'product_uom_id': fields.related('product_id', 'uom_id', type='many2one', relation='product.uom', string="Default Unit Of Measure", readonly="1"),
        'product_categ_id': fields.related('product_id', 'categ_id', type='many2one', relation='product.category', string="Category"),
    }
    
    _defaults = {
        'quantity': 1.0,
    }

product_pack_sale()

class product_pack_purchase( osv.osv ):
    _name = 'product.pack.purchaseline'
    _rec_name = 'product_id'
    _columns = {
        'parent_product_id': fields.many2one('product.product', 'Parent Product', ondelete='cascade', required=True),
        'quantity': fields.float('Quantity', required=True ),
        'product_id': fields.many2one('product.product', 'Product', required=True ),   
        'product_name': fields.related('product_id', 'name', type='char', string='Name'),
        'product_code': fields.related('product_id', 'default_code', type='char', string='Default code'),
        'product_uom_id': fields.related('product_id', 'uom_po_id', type='many2one', relation='product.uom', string="Purchase Unit of Measure", readonly="1"),
        'product_categ_id': fields.related('product_id', 'categ_id', type='many2one', relation='product.category', string="Category"),
    }
    
    _defaults = {
        'quantity': 1.0,
    }

product_pack_purchase()

class product_product( osv.osv ):
    _inherit = 'product.product'
    _columns = {
        'stock_depends': fields.boolean( 'Stock depends of components', help='Mark if pack stock is calculated from component stock' ),       
        'sale_pack_line_ids': fields.one2many('product.pack.saleline','parent_product_id', 'Pack Products', help='List of products that are part of this pack.' ),
        'fixed_sale_price': fields.boolean('Pack has fixed price', help='Mark this field if the price of the pack should be fixed. Do not mark it if the price should be calculated from the sum of the prices of the products in the pack.' ),
        'purchase_pack_line_ids': fields.one2many('product.pack.purchaseline','parent_product_id', 'Pack Products', help='List of products that are part of this pack.' ),
        'fixed_purchase_price': fields.boolean('Pack has fixed price', help='Mark this field if the price of the pack should be fixed. Do not mark it if the price should be calculated from the sum of the prices of the products in the pack.' ),
    }   
    
    _defaults = {
        'fixed_sale_price': True,
        'fixed_purchase_price': True,
    }

    def get_product_available( self, cr, uid, ids, context=None ):
        """ Calulate stock for packs, return  maximum stock that lets complete pack """
        result={}
        for product in self.browse( cr, uid, ids, context=context ):
            stock = super( product_product, self ).get_product_available( cr, uid, [ product.id ], context=context )

            # Check if product stock depends on it's subproducts stock.
            if not product.stock_depends:
                result[ product.id ] = stock[ product.id ]
                continue

            first_subproduct = True
            pack_stock = 0
            
            pack_line_ids = None
            if product.sale_pack_line_ids:
                pack_line_ids = product.sale_pack_line_ids
            else:
                if product.purchase_pack_line_ids:
                    pack_line_ids = product.purchase_pack_line_ids
                  

            # Check if the pack has subproducts
            if pack_line_ids:
                # Take the stock/virtual stock of all subproducts
                subproducts_stock = self.get_product_available( cr, uid, [ line.product_id.id for line in pack_line_ids ], context=context )
                # Go over all subproducts, take quantity needed for the pack and its available stock
                for subproduct in pack_line_ids:
                    if first_subproduct:
                        subproduct_quantity = subproduct.quantity
                        subproduct_stock = subproducts_stock[ subproduct.product_id.id ]
                        # Calculate real stock for current pack from the subproduct stock and needed quantity
                        pack_stock = math.floor( subproduct_stock / subproduct_quantity )
                        first_subproduct = False
                        continue
                    # Take the info of the next subproduct
                    subproduct_quantity_next = subproduct.quantity
                    subproduct_stock_next = subproducts_stock[ subproduct.product_id.id ]
                    pack_stock_next = math.floor( subproduct_stock_next / subproduct_quantity_next )
                    # compare the stock of a subproduct and the next subproduct
                    if pack_stock_next < pack_stock:
                        pack_stock = pack_stock_next
                # result is the minimum stock of all subproducts
                result[ product.id ] = pack_stock
            else:
                result[ product.id ] = stock[ product.id ]
        return result

product_product()

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'pack_depth': fields.integer('Depth', required=True, help='Depth of the product if it is part of a pack.'),
        'pack_parent_line_id': fields.many2one('sale.order.line', 'Pack', help='The pack that contains this product.'),
        'pack_child_line_ids': fields.one2many('sale.order.line', 'pack_parent_line_id', 'Lines in pack', help=''),
        'pack_expand': fields.boolean( 'Pack expand', help='If checked, the product pack will be automatically expanded when computed' ),
    }
    _defaults = {
        'pack_depth': lambda *a: 0,
        'pack_expand': True,
    }
    
    def create(self, cr, user, vals, context=None):
        result = False
        result = super(sale_order_line, self).create(cr, user, vals, context)  
        return result
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
			
        default.update({'pack_child_line_ids':False, 'pack_depth':0})
        result = super(sale_order_line, self).copy_data(cr, uid, id, default, context=context) 
        if result.get('pack_parent_line_id', False) <> False:
            result['pack_delete'] = True
        
        return result
    
sale_order_line()

class sale_order(osv.osv):
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        result = super(sale_order,self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(sale_order,self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result
    
    def copy(self, cr, uid, ids, vals, context=None):
        result = super(sale_order,self).copy(cr, uid, ids, vals, context)
        return result
    
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}

        result = super(sale_order, self).copy_data(cr, uid, id, default, context=context) 
        
        def copy_data_filter(line):
            # line is tuple with data a position 3 tuple(0,0,{})
            return line[2].get('pack_delete', False) 
         
        if result.has_key('abstract_line_ids'):  
            # We create a list comprehension by filtering data and removing lines to delete
            result['abstract_line_ids'] = [x for x in result['abstract_line_ids'] if not copy_data_filter(x)]

        return result

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):
            
            fiscal_position = order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, order.fiscal_position, context) or False

            # The reorder variable is used to ensure lines of the same pack go right after their 
            # parent.
            # What the algorithm does is check if the previous item had children. As children items 
            # must go right after the parent if the line we're evaluating doesn't have a parent it
            # means it's a new item (and probably has the default 10 sequence number - unless the 
            # appropiate c2c_sale_sequence module is installed). In this case we mark the item for
            # reordering and evaluate the next one. Note that as the item is not evaluated and it might
            # have to be expanded it's put on the queue for another iteration (it's simple and works well).
            # Once the next item has been evaluated the sequence of the item marked for reordering is updated
            # with the next value.
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append( line.id )
                    if line.product_id.sale_pack_line_ids and not order.id in updated_orders:
                        updated_orders.append( order.id )
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('sale.order.line').write(cr, uid, [line.id], {'sequence': sequence,}, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                # If pack was already expanded (in another create/write operation or in 
                # a previous iteration) don't do it again.
                if not line.pack_expand or line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.sale_pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_uom_qty

                    if line.product_id.fixed_sale_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], 
                                        subproduct.id, quantity, order.partner_id.id, {
                            'uom': subproduct.uom_id.id,
                            'date': order.date_order,
                        })[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.product').browse(cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s %s' % ('>'* (line.pack_depth+1), subproduct_name),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        'procurement_id': line.procurement_id and line.procurement_id.id or False,
                        'price_unit': price,
                        'tax_id': [(6,0,tax_ids)],
                        'type': subproduct.procure_method,
                        'property_ids': [(6,0,[])],
                        'address_allotment_id': False,
                        'product_uom_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'move_ids': [(6,0,[])],
                        'discount': discount,
                        'number_packages': False,
                        'notes': subproduct.description_sale,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    # It's a control for the case that the nan_external_prices was installed with the product pack
                    if 'prices_used' in line:
                        vals[ 'prices_used' ] = line.prices_used

                    self.pool.get('sale.order.line').create(cr, uid, vals, context)
                    if not order.id in updated_orders:
                        updated_orders.append( order.id )

                for id in reorder:
                    sequence += 1
                    self.pool.get('sale.order.line').write(cr, uid, [id], {'sequence': sequence,}, context)

        if updated_orders:
            # Try to expand again all those orders that had a pack in this iteration.
            # This way we support packs inside other packs.
            self.expand_packs(cr, uid, ids, context, depth+1)
        return

sale_order()


class purchase_order_line(osv.osv):
    _inherit = 'purchase.order.line'
    _columns = {
        'sequence': fields.integer('Sequence', help="Gives the sequence order when displaying a list of purchase order lines."),
        'pack_depth': fields.integer('Depth', required=True, help='Depth of the product if it is part of a pack.'),
        'pack_parent_line_id': fields.many2one('purchase.order.line', 'Pack', help='The pack that contains this product.'),
        'pack_child_line_ids': fields.one2many('purchase.order.line', 'pack_parent_line_id', 'Lines in pack', help=''),
        'pack_expand': fields.boolean( 'Pack expand', help='If checked, the product pack will be automatically expanded when computed' ),
        'pack_print': fields.boolean( 'Pack print', help='If checked, the product pack content will be print' ),
    }
    _defaults = {
        'pack_depth': lambda *a: 0,
        'pack_expand': True,
        'pack_print': True,
    }
    
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}
            
        default.update({'pack_child_line_ids':False, 'pack_depth':0})
        result = super(purchase_order_line, self).copy_data(cr, uid, id, default, context=context) 
        if result.get('pack_parent_line_id', False) <> False:
            result['pack_delete'] = True
        
        return result
    
purchase_order_line()


class purchase_order(osv.osv):
    _inherit = 'purchase.order'

    def create(self, cr, uid, vals, context=None):
        result = super(purchase_order,self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(purchase_order,self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result
    
    
    def copy_data(self, cr, uid, id, default=None, context=None):
        if default is None:
            default = {}

        result = super(purchase_order, self).copy_data(cr, uid, id, default, context=context) 
        
        def copy_data_filter(line):
            # line is tuple with data a position 3 tuple(0,0,{})
            return line[2].get('pack_delete', False) 
         
        if result.has_key('order_line'):  
            # We create a list comprehension by filtering data and removing lines to delete
            result['order_line'] = [x for x in result['order_line'] if not copy_data_filter(x)]

        return result

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):
            
            fiscal_position = order.fiscal_position and self.pool.get('account.fiscal.position').browse(cr, uid, order.fiscal_position, context) or False

            # The reorder variable is used to ensure lines of the same pack go right after their 
            # parent.
            # What the algorithm does is check if the previous item had children. As children items 
            # must go right after the parent if the line we're evaluating doesn't have a parent it
            # means it's a new item (and probably has the default 10 sequence number - unless the 
            # appropiate c2c_sale_sequence module is installed). In this case we mark the item for
            # reordering and evaluate the next one. Note that as the item is not evaluated and it might
            # have to be expanded it's put on the queue for another iteration (it's simple and works well).
            # Once the next item has been evaluated the sequence of the item marked for reordering is updated
            # with the next value.
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append( line.id )
                    if line.product_id.purchase_pack_line_ids and not order.id in updated_orders:
                        updated_orders.append( order.id )
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('purchase.order.line').write(cr, uid, [line.id], {
                        'sequence': sequence,
                    }, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                # If pack was already expanded (in another create/write operation or in 
                # a previous iteration) don't do it again.
                if not line.pack_expand or line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.purchase_pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_qty

                    if line.product_id.fixed_purchase_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(cr, uid, [pricelist], subproduct.id, quantity, order.partner_id.id, {
                            'uom': subproduct.uom_id.id,
                            'date': order.date_order,
                        })[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.product').browse(cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s %s' % ('>'* (line.pack_depth+1), subproduct_name),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        #'procurement_id': line.procurement_id and line.procurement_id.id or False,
                        'date_planned': line.date_planned,
                        'price_unit': price,
                        'taxes_id': [(6,0,tax_ids)],
                        'type': subproduct.procure_method,
                        'property_ids': [(6,0,[])],
                        'address_allotment_id': False,
                        'product_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'move_ids': [(6,0,[])],
                        'discount': discount,
                        'number_packages': False,
                        'notes': False,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    # It's a control for the case that the nan_external_prices was installed with the product pack
                    if 'prices_used' in line:
                        vals[ 'prices_used' ] = line.prices_used

                    self.pool.get('purchase.order.line').create(cr, uid, vals, context)
                    if not order.id in updated_orders:
                        updated_orders.append( order.id )

                for id in reorder:
                    sequence += 1
                    self.pool.get('purchase.order.line').write(cr, uid, [id], {
                        'sequence': sequence,
                    }, context)

        if updated_orders:
            # Try to expand again all those orders that had a pack in this iteration.
            # This way we support packs inside other packs.
            self.expand_packs(cr, uid, ids, context, depth+1)
        return
    

    def line_refresh_price(self, order, line, context=None):
        if line.pack_parent_line_id:
            result = line.price_unit
        else:
            result = super(purchase_order, self).line_refresh_price(order, line, context)
        return result

    def action_fix_extend_pack_pickings(self, cr, uid, ids, context=None): 
        for order in self.browse(cr, uid, ids):
            self._extend_pack_pickings(cr, uid, order, order.order_line, context)
            
        return True

    def _extend_pack_pickings(self, cr, uid, order, order_lines, context=None):  
    
        def get_final_move(move):
            if move.move_dest_id and (move.product_id.id == move.move_dest_id.product_id.id): 
                return get_final_move(move.move_dest_id)   
            else:
                return move   
            
        def recursive_action_done(move):
            move.action_done() 
            if move.move_dest_id and (move.product_id.id == move.move_dest_id.product_id.id):
                recursive_action_done(move.move_dest_id)   
            
        stock_move_obj = self.pool.get('stock.move')
        mrp_production_obj = self.pool.get('mrp.production')
                
        
        # Create a new move with the same destination that the parent move 
        for order_line in order_lines:
            final_move = False
            production_ids = []
            if order_line.pack_child_line_ids:
                procurement_move = order_line.origin_procurement_order_id and order_line.origin_procurement_order_id.move_id 
                final_move = get_final_move(procurement_move)
                picking = procurement_move and procurement_move.picking_id 
                assert (picking <> False) 
                
                if picking.type == 'internal': 
                    # Get production order from PTN data
                    production_ids = mrp_production_obj.search(cr, uid, [('picking_id', '=', picking.id)], context=context)
                    # If the move comes from REFManager, we need to get it from production move data
                    if not production_ids:
                        production_ids = mrp_production_obj.search(cr, uid, [('move_all_src_ids', '=', procurement_move.id)], context=context)  
                    # YP: 14-05-2014: Remove assertion since it could be made only a procurement for STOCK
                    # But there is a stock error in that case, maybe just deleting the pack line is enought
                    # YP: 04-05-2015: Maybe it is just a human error, the valid workflow should be 
                    # sale-purchase-send or production-purchase-send
                    assert(production_ids <> [])
                elif picking.type == 'in': 
                    pass
                elif picking.type == 'out': 
                    pass
                
            if final_move:  
                logging.getLogger('purchase.order').info('Extend picking for purchase %s: %s', order.name, order_line.product_id.name_get()[0][1]) 
                for child in order_line.pack_child_line_ids:
                    child_move_ids = [move for move in child.move_ids if move.state <> 'cancel' and not move.move_dest_id]
                    if child_move_ids:
                        # Create a new move with the same data that the purchase one 
                        child_purchase_move = child_move_ids[0]  
                        default = {
                            'name': '%s: %s' % (final_move.name, final_move.product_id.default_code or final_move.product_id.name or ''),
                            'picking_id': False, 
                            'auto_validate': True,
                            'address_id': False,
                            'move_dest_id': final_move.id,
                            'location_id': child_purchase_move.location_dest_id.id,
                            'location_dest_id': final_move.location_dest_id.id,   
                            'state': 'confirmed',   
                            'purchase_line_id': False,  
                            'price_unit': False,     
                        }
                        if picking.type == 'out': 
                            default['picking_id'] = picking and picking.id
                            
                        new_move_id = stock_move_obj.copy(cr, uid, child_purchase_move.id, default, context=context)
                        child_purchase_move.write({'move_dest_id': new_move_id})
                        
                        if production_ids: 
                            # Attach the new move to the same production order
                            mrp_production_obj.write(cr, uid, production_ids, {'move_all_src_ids': [(4, new_move_id)]}, context=context)  
                            
                        # Finalize the new stock move if the pack is done
                        if child_purchase_move.state == 'done':   
                            stock_move_obj.browse(cr, uid, new_move_id, context=context).action_done()
                            stock_move_obj.write(cr, uid, new_move_id, {'date': child_purchase_move.date,'create_date': child_purchase_move.create_date}, context=context)
                      
            # Instant finalize reception of the pack himself
            if order_line.pack_child_line_ids:  
                for purchase_move in order_line.move_ids:
                    recursive_action_done(purchase_move)
                    
    def _create_pickings(self, cr, uid, order, order_lines, picking_id=False, context=None):  
        result = super(purchase_order, self)._create_pickings(cr, uid, order, order_lines, picking_id, context)
        self._extend_pack_pickings(cr, uid, order, order_lines, context)  
        return result

purchase_order()


class product_template(osv.osv):
    _name = "product.template"
    _inherit = _name
    
    def write(self, cr, uid, ids, vals, context=None):
        if 'uom_po_id' in vals:
            pack_saleline_obj = self.pool.get('product.pack.saleline')
            pack_purchaseline_obj = self.pool.get('product.pack.purchaseline')
            new_uom = self.pool.get('product.uom').browse(cr, uid, vals['uom_po_id'], context=context)
            if new_uom:
                for product in self.browse(cr, uid, ids, context=context):
                    old_uom = product.uom_po_id
                    pack_saleline_ids = pack_saleline_obj.search(cr, uid, [('product_id', '=', product.id)], context=context)
                    pack_purchaseline_ids = pack_purchaseline_obj.search(cr, uid, [('product_id', '=', product.id)], context=context)
                    if (old_uom.category_id.id != new_uom.category_id.id) and (pack_saleline_ids or pack_purchaseline_ids):
                        raise osv.except_osv(_('UoM categories Mismatch!'), 
                                             _('This product is used in a pack (%s,%s)') % (str(pack_saleline_ids), str(pack_purchaseline_ids)) + '\n\n' +
                                             _("New UoM '%s' must belong to same UoM category '%s' as of old UoM '%s'. If you need to change the unit of measure, you may desactivate this product from the 'Procurement & Locations' tab and create a new one.") % (new_uom.name, old_uom.category_id.name, old_uom.name,))
        return super(product_template, self).write(cr, uid, ids, vals, context=context)

    
