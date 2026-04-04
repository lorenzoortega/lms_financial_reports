from odoo import models, fields, api


class AgingReceivableSummaryLine(models.TransientModel):
    _name = 'lms.aging.receivable.summary.line'
    _description = 'Líneas Balance por Antigüedad Resumido'
    _order = 'sequence asc, id asc'

    wizard_id = fields.Many2one('lms.aging.receivable.summary.wizard', ondelete='cascade')
    sequence = fields.Integer(default=10)

    partner_id = fields.Many2one('res.partner', string='Cliente')
    customer_name = fields.Char(string='Cliente')

    balance_pending = fields.Float(string='Balance Pendiente')
    not_due = fields.Float(string='No Vencida')
    bucket_1_30 = fields.Float(string='1-30')
    bucket_31_60 = fields.Float(string='31-60')
    bucket_61_90 = fields.Float(string='61-90')
    bucket_90_plus = fields.Float(string='90+')

    is_total = fields.Boolean(default=False)
    total_label = fields.Char(string='Etiqueta Total')

    row_label = fields.Char(string='Cliente', compute='_compute_row_label', store=False)

    @api.depends('is_total', 'total_label', 'customer_name')
    def _compute_row_label(self):
        for rec in self:
            rec.row_label = rec.total_label if rec.is_total else (rec.customer_name or '')