from odoo import models, fields, api, _
from odoo.exceptions import UserError


class PosReportLine(models.TransientModel):
    _name = 'lms.pos.report.line'
    _description = 'Líneas Reporte POS'
    _order = 'sequence, id'

    wizard_id = fields.Many2one(
        'lms.pos.report.wizard',
        ondelete='cascade'
    )

    sequence = fields.Integer(default=10)

    is_group = fields.Boolean(default=False)
    is_subtotal = fields.Boolean(default=False)

    row_type = fields.Selection(
        [
            ('group', 'Grupo'),
            ('subtotal', 'Subtotal'),
            ('line', 'Línea'),
        ],
        compute='_compute_row_type',
        store=False,
    )

    group_name = fields.Char(string="Cabecera de Sesión")
    date_label = fields.Char(string="Fecha / Sesión", compute='_compute_date_label', store=False)

    date = fields.Datetime(string="Fecha")
    pos_name = fields.Char(string="Punto de Venta")
    session_name = fields.Char(string="Sesión")
    session_state = fields.Char(string="Estado Sesión")
    cashier_name = fields.Char(string="Cajero")
    order_name = fields.Char(string="Orden POS")
    invoice_name = fields.Char(string="Factura")
    ncf_number = fields.Char(string="NCF")
    customer_name = fields.Char(string="Cliente")
    payment_method_name = fields.Char(string="Método de Pago")
    amount = fields.Float(string="Monto")

    session_id = fields.Many2one('pos.session', string="Sesión POS")
    order_id = fields.Many2one('pos.order', string="Orden POS")
    invoice_id = fields.Many2one('account.move', string="Factura")

    @api.depends('is_group', 'is_subtotal')
    def _compute_row_type(self):
        for rec in self:
            if rec.is_group:
                rec.row_type = 'group'
            elif rec.is_subtotal:
                rec.row_type = 'subtotal'
            else:
                rec.row_type = 'line'

    @api.depends('is_group', 'is_subtotal', 'group_name', 'date')
    def _compute_date_label(self):
        for rec in self:
            if rec.is_group:
                rec.date_label = rec.group_name or ''
            elif rec.is_subtotal:
                rec.date_label = "SUBTOTAL SESIÓN"
            else:
                rec.date_label = fields.Datetime.to_string(rec.date) if rec.date else ''

    def action_open_invoice(self):
        self.ensure_one()

        if self.is_group or self.is_subtotal or not self.invoice_id:
            raise UserError(_("Esta fila no corresponde a una factura navegable."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Factura %s') % (self.invoice_id.name or ''),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
