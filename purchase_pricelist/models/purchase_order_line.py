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

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # _get_display_price is inspired from the 'sale.order.line'
    # same name function
    @api.multi
    def _get_display_price(self, product):
        # For purchase pricelists, we don't care about the discount_policy
        # We always return the discounted price
        product = product.with_context(pricelist=self.order_id.pricelist_id.id)
        return product.price

    # _onchange_quantity is inspired from the 'sale.order.line'
    # product_id_change function
    @api.onchange('product_qty', 'product_uom')
    def _onchange_quantity(self):
        super()._onchange_quantity()
        if self.product_id and self.order_id.pricelist_id and self.order_id.partner_id:
            Tax = self.env['account.tax']
            product = self.product_id.with_context(
                lang=self.order_id.partner_id.lang,
                partner=self.order_id.partner_id,
                quantity=self.product_uom_qty,
                date=self.order_id.date_order,
                pricelist=self.order_id.pricelist_id.id,
                uom=self.product_uom.id,
                fiscal_position=self.env.context.get('fiscal_position')
            )
            self.price_unit = Tax._fix_tax_included_price_company(
                self._get_display_price(product),
                product.supplier_taxes_id,
                self.taxes_id,
                self.company_id,
            )

    def _suggest_quantity(self):
        super()._suggest_quantity()