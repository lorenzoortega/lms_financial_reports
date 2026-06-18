from odoo import models, fields, api


class PosCashClosingActLine(models.TransientModel):
    _name = 'lms.pos.cash.closing.act.line'
    _description = 'Líneas Acta de Cierre Caja POS'
    _order = 'sequence asc, id asc'

    wizard_id = fields.Many2one('lms.pos.cash.closing.act.wizard', ondelete='cascade')
    sequence = fields.Integer(default=10)
    is_total = fields.Boolean(default=False)

    date = fields.Date(string="Fecha")
    pos_name = fields.Char(string="Punto de Venta")
    session_name = fields.Char(string="Sesión")
    session_state = fields.Char(string="Estado")
    cashier_name = fields.Char(string="Cajero")
    opening_time = fields.Char(string="Apertura")
    closing_time = fields.Char(string="Cierre")
    order_count = fields.Integer(string="Órdenes")

    cash_amount = fields.Float(string="Efectivo Sistema")
    driver_liquidation_amount = fields.Float(string="Liquidación Chofer")
    total_cash_expected = fields.Float(string="Efectivo Esperado")
    cash_counted = fields.Float(string="Efectivo Contado")
    cash_difference = fields.Float(string="Diferencia")
    has_cash_counted = fields.Boolean(string="Tiene Cierre")

    card_amount = fields.Float(string="Tarjeta")
    transfer_amount = fields.Float(string="Transferencia")
    other_amount = fields.Float(string="Otros")
    total_collected = fields.Float(string="Total Cobrado")
    result_label = fields.Char(string="Resultado")

    order_count_display = fields.Char(string="Órdenes", compute='_compute_display_fields')
    cash_amount_display = fields.Char(string="Efectivo Sistema", compute='_compute_display_fields')
    driver_liquidation_amount_display = fields.Char(string="Liquidación Chofer", compute='_compute_display_fields')
    total_cash_expected_display = fields.Char(string="Efectivo Esperado", compute='_compute_display_fields')
    cash_counted_display = fields.Char(string="Efectivo Contado", compute='_compute_display_fields')
    cash_difference_display = fields.Char(string="Diferencia", compute='_compute_display_fields')
    card_amount_display = fields.Char(string="Tarjeta", compute='_compute_display_fields')
    transfer_amount_display = fields.Char(string="Transferencia", compute='_compute_display_fields')
    other_amount_display = fields.Char(string="Otros", compute='_compute_display_fields')
    total_collected_display = fields.Char(string="Total Cobrado", compute='_compute_display_fields')

    @api.depends(
        'order_count', 'cash_amount', 'driver_liquidation_amount', 'total_cash_expected',
        'cash_counted', 'cash_difference', 'card_amount', 'transfer_amount', 'other_amount',
        'total_collected', 'has_cash_counted'
    )
    def _compute_display_fields(self):
        for rec in self:
            rec.order_count_display = str(rec.order_count or 0)
            rec.cash_amount_display = f"{rec.cash_amount:,.2f}"
            rec.driver_liquidation_amount_display = f"{rec.driver_liquidation_amount:,.2f}"
            rec.total_cash_expected_display = f"{rec.total_cash_expected:,.2f}"
            rec.card_amount_display = f"{rec.card_amount:,.2f}"
            rec.transfer_amount_display = f"{rec.transfer_amount:,.2f}"
            rec.other_amount_display = f"{rec.other_amount:,.2f}"
            rec.total_collected_display = f"{rec.total_collected:,.2f}"

            if rec.has_cash_counted or rec.is_total:
                rec.cash_counted_display = f"{rec.cash_counted:,.2f}"
                rec.cash_difference_display = f"{rec.cash_difference:,.2f}"
            else:
                rec.cash_counted_display = ''
                rec.cash_difference_display = ''
