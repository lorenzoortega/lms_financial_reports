from odoo import models, fields, api


class PosDailyReportLine(models.TransientModel):
    _name = 'lms.pos.daily.report.line'
    _description = 'Líneas Reporte Ventas POS Día'
    _order = 'sequence asc, id asc'

    wizard_id = fields.Many2one(
        'lms.pos.daily.report.wizard',
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

    date_label = fields.Char(string="Fecha / POS", compute='_compute_date_label', store=False)
    group_name = fields.Char(string="Cabecera")
    subtotal_label = fields.Char(string="Etiqueta Total")

    date = fields.Date(string="Fecha")
    session_range = fields.Char(string="Rango Sesión")
    session_name = fields.Char(string="Sesión")
    session_state = fields.Char(string="Estado")
    cashier_name = fields.Char(string="Cajero")
    order_count = fields.Integer(string="Cant. Órdenes")

    cash_amount = fields.Float(string="Efectivo")
    driver_liquidation_amount = fields.Float(string="Liquidación Chofer")
    total_cash_collected = fields.Float(string="Total Efectivo Cobrado")
    cash_counted = fields.Float(string="Efectivo Contado")
    cash_difference = fields.Float(string="Diferencia Efectivo")
    has_cash_counted = fields.Boolean(string="Tiene Efectivo Contado", default=False)

    card_amount = fields.Float(string="Tarjeta")
    transfer_amount = fields.Float(string="Transferencia")
    total_sales = fields.Float(string="TOTAL VENTAS")

    pos_name = fields.Char(string="Punto de Venta")
    session_id = fields.Many2one('pos.session', string="Sesión POS")
    pos_config_id = fields.Many2one('pos.config', string="Punto de Venta")
    cashier_id = fields.Many2one('res.users', string="Cajero")

    # Campos display para evitar mostrar 0.00 en filas cabecera
    order_count_display = fields.Char(string="Cant. Órdenes", compute='_compute_display_fields', store=False)
    cash_amount_display = fields.Char(string="Efectivo", compute='_compute_display_fields', store=False)
    driver_liquidation_amount_display = fields.Char(string="Liquidación Chofer", compute='_compute_display_fields', store=False)
    total_cash_collected_display = fields.Char(string="Total Efectivo Cobrado", compute='_compute_display_fields', store=False)
    cash_counted_display = fields.Char(string="Efectivo Contado", compute='_compute_display_fields', store=False)
    cash_difference_display = fields.Char(string="Diferencia Efectivo", compute='_compute_display_fields', store=False)
    card_amount_display = fields.Char(string="Tarjeta", compute='_compute_display_fields', store=False)
    transfer_amount_display = fields.Char(string="Transferencia", compute='_compute_display_fields', store=False)
    total_sales_display = fields.Char(string="TOTAL VENTAS", compute='_compute_display_fields', store=False)

    @api.depends('is_group', 'is_subtotal')
    def _compute_row_type(self):
        for rec in self:
            if rec.is_group:
                rec.row_type = 'group'
            elif rec.is_subtotal:
                rec.row_type = 'subtotal'
            else:
                rec.row_type = 'line'

    @api.depends('is_group', 'is_subtotal', 'group_name', 'subtotal_label', 'date')
    def _compute_date_label(self):
        for rec in self:
            if rec.is_group:
                rec.date_label = rec.group_name or ''
            elif rec.is_subtotal:
                rec.date_label = rec.subtotal_label or 'TOTAL'
            else:
                rec.date_label = str(rec.date or '')

    @api.depends(
        'is_group', 'is_subtotal', 'has_cash_counted',
        'order_count',
        'cash_amount', 'driver_liquidation_amount', 'total_cash_collected',
        'cash_counted', 'cash_difference',
        'card_amount', 'transfer_amount', 'total_sales'
    )
    def _compute_display_fields(self):
        for rec in self:
            if rec.is_group:
                rec.order_count_display = ''
                rec.cash_amount_display = ''
                rec.driver_liquidation_amount_display = ''
                rec.total_cash_collected_display = ''
                rec.cash_counted_display = ''
                rec.cash_difference_display = ''
                rec.card_amount_display = ''
                rec.transfer_amount_display = ''
                rec.total_sales_display = ''
            else:
                rec.order_count_display = str(rec.order_count or 0)
                rec.cash_amount_display = f"{rec.cash_amount:,.2f}"
                rec.driver_liquidation_amount_display = f"{rec.driver_liquidation_amount:,.2f}"
                rec.total_cash_collected_display = f"{rec.total_cash_collected:,.2f}"

                if rec.has_cash_counted or rec.is_subtotal:
                    rec.cash_counted_display = f"{rec.cash_counted:,.2f}"
                    rec.cash_difference_display = f"{rec.cash_difference:,.2f}"
                else:
                    rec.cash_counted_display = ''
                    rec.cash_difference_display = ''

                rec.card_amount_display = f"{rec.card_amount:,.2f}"
                rec.transfer_amount_display = f"{rec.transfer_amount:,.2f}"
                rec.total_sales_display = f"{rec.total_sales:,.2f}"