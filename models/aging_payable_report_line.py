from odoo import models, fields


class AgingPayableReportLine(models.TransientModel):
    _name = 'lms.aging.payable.report.line'
    _description = 'Balance Antigüedad Proveedores - Detalle'
    _order = 'sequence asc'

    wizard_id = fields.Many2one('lms.aging.payable.report.wizard', ondelete='cascade')

    sequence = fields.Integer()
    is_group = fields.Boolean()
    is_subtotal = fields.Boolean()

    group_name = fields.Char()
    subtotal_label = fields.Char()

    vendor_name = fields.Char(string="Proveedor")
    partner_id = fields.Many2one('res.partner')

    invoice_id = fields.Many2one('account.move')
    invoice_name = fields.Char(string="Factura")

    invoice_date = fields.Date(string="Fecha Factura")
    due_date = fields.Date(string="Vencimiento")

    balance_pending = fields.Float(string="Balance Pendiente")
    days_overdue = fields.Integer(string="Días Vencidos")

    not_due = fields.Float(string="No Vencida")
    bucket_1_30 = fields.Float(string="1-30")
    bucket_31_60 = fields.Float(string="31-60")
    bucket_61_90 = fields.Float(string="61-90")
    bucket_90_plus = fields.Float(string="90+")