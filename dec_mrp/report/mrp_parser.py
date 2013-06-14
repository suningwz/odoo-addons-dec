# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
from datetime import datetime, timedelta
from dateutil.rrule import *
from dateutil.relativedelta import relativedelta
from report import report_sxw
from tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT, float_compare
from tools.translate import _

class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(Parser, self).__init__(cr, uid, name, context=context)
        self.localcontext.update({
            'time': time,
            'manufacturer': self.get_manufacturer,
            'date_procurement': self.get_date_procurement,
            'date_shipping': self.get_date_shipping,
        })
        self.context = context

    def get_manufacturer(self, product):
        res = ''
        categ_id = product.categ_id
        if categ_id:
            while categ_id.parent_id and (categ_id.parent_id.id <> 1):
                categ_id = categ_id.parent_id

            if categ_id <> product.categ_id:
                res = ('%s - %s') % (categ_id.name, product.categ_id.name)
            else:
                res = ('%s') % (categ_id.name) 

        return res
        
    def get_date_procurement(self, production):
         
        product = production.product_id 
        if product.sale_delay and product.produce_delay and (product.sale_delay >= product.produce_delay):
            working_delay = product.sale_delay-product.produce_delay 
            if working_delay >= 5:
                delay = working_delay*7/5
            else:
                delay = working_delay
                 
            dtstart = datetime.strptime(production.date_planned, DEFAULT_SERVER_DATETIME_FORMAT) - relativedelta(days=delay)
            #result = list(rrule(DAILY, count=1+(working_delay or 0.0), byweekday=(MO,TU,WE,TH,FR), dtstart=dtstart))[-1] 
            return dtstart 
        else:
            return production.date_planned 
            
         
    def get_date_shipping(self, production):   
        
        product = production.product_id 
        if product.produce_delay:
            dtstart = datetime.strptime(production.date_planned, DEFAULT_SERVER_DATETIME_FORMAT)
            dtshipping = list(rrule(DAILY, count=1+(product.produce_delay or 0.0), byweekday=(MO,TU,WE,TH,FR), dtstart=dtstart))[-1] 
            return dtshipping
        else:
            return production.date_planned 
        
        