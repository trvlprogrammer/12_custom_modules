import logging
_logger = logging.getLogger(__name__)

from datetime import datetime

from odoo import api, models, fields

class Migration_Invoice(models.Model):
    _inherit = 'account.invoice'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_original_due = fields.Monetary(string='Original Due Amount', translate=False, readonly=True)
    mig_original_id = fields.Integer(string='Original ID', translate=False, readonly=True)

class Migration_SO_line(models.Model):
    _inherit = 'sale.order.line'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)

class Migration_SO(models.Model):
    _inherit = 'sale.order'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_original_due = fields.Monetary(string='Original Due Amount', translate=False, readonly=True)
    mig_original_id = fields.Integer(string='Original ID', translate=False, readonly=True)

class Migration_PO(models.Model):
    _inherit = 'purchase.order'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_original_due = fields.Monetary(string='Original Due Amount', translate=False, readonly=True)
    mig_original_id = fields.Integer(string='Original ID', translate=False, readonly=True)

class Migration_Product_Product(models.Model):
    _inherit = 'product.product'
    
    mig_original_id = fields.Integer(string='Original ID', translate=False, readonly=True)

class Migration_Product_Templ(models.Model):
    _inherit = 'product.template'
    
    mig_original_id = fields.Integer(string='Original ID', translate=False, readonly=True)
   

class Migration_Payment(models.Model):
    _inherit = 'account.payment'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)


class Migration_Picking(models.Model):
    _inherit = 'stock.picking'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_current_step = fields.Char(string='Current Step', translate=False, readonly=True)
    mig_row_status = fields.Char(string='Row Status', translate=False, readonly=True)


class Migration_LandedCost(models.Model):    
    _inherit = 'stock.landed.cost'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)    


class Migration_PickingMove(models.Model):
    _inherit = 'stock.move'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_original_done = fields.Integer(string='Original Done', translate=False, readonly=True)


class Migration_PickingLoveLine(models.Model):
    _inherit = 'stock.move.line'
    
    mig_original_state = fields.Char(string='Original State', translate=False, readonly=True)
    mig_original_done = fields.Integer(string='Original Done', translate=False, readonly=True)
