from odoo import models, fields, api


class AgingReceivableReportLine(models.TransientModel):
    _name = 'lms.aging.receivable.report.line'
    _description = 'Líneas Balance por Antigüedad'
    _order = 'sequence asc, id asc'

    wizard_id = fields.Many2one('lms.aging.receivable.report.wizard', ondelete='cascade')
    sequence = fields.Integer(default=10)

    is_group = fields.Boolean(default=False)
    is_subtotal = fields.Boolean(default=False)

    group_name = fields.Char(string='Grupo')
    subtotal_label = fields.Char(string='Subtotal')

    partner_id = fields.Many2one('res.partner', string='Cliente')
    customer_name = fields.Char(string='Cliente')

    invoice_id = fields.Many2one('account.move', string='Factura')
    invoice_name = fields.Char(string='Factura')
    invoice_date = fields.Date(string='Fecha Factura')
    due_date = fields.Date(string='Vencimiento')

    balance_pending = fields.Float(string='Balance Pendiente')
    days_overdue = fields.Integer(string='Días Vencidos')

    not_due = fields.Float(string='No Vencida')
    bucket_1_30 = fields.Float(string='1-30')
    bucket_31_60 = fields.Float(string='31-60')
    bucket_61_90 = fields.Float(string='61-90')
    bucket_90_plus = fields.Float(string='90+')

    row_label = fields.Char(string='Cliente / Concepto', compute='_compute_row_label', store=False)

    @api.depends('is_group', 'is_subtotal', 'group_name', 'subtotal_label', 'customer_name')
    def _compute_row_label(self):
        for rec in self:
            if rec.is_group:
                rec.row_label = rec.group_name or rec.customer_name or ''
            elif rec.is_subtotal:
                rec.row_label = rec.subtotal_label or ''
            else:
                rec.row_label = rec.customer_name or ''