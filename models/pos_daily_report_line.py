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
    cxc_receipt_count = fields.Integer(string="Recibos CxC")

    cash_amount = fields.Float(string="Efectivo POS")
    driver_liquidation_amount = fields.Float(string="Liquidación Chofer")
    cxc_cash_amount = fields.Float(string="Efectivo CxC")
    total_cash_collected = fields.Float(string="Total Efectivo Cobrado")
    cash_counted = fields.Float(string="Efectivo Contado")
    cash_difference = fields.Float(string="Diferencia Efectivo")
    has_cash_counted = fields.Boolean(string="Tiene Efectivo Contado", default=False)

    card_amount = fields.Float(string="Tarjeta POS")
    cxc_card_amount = fields.Float(string="Tarjeta CxC")
    total_card_collected = fields.Float(string="Total Tarjeta")
    transfer_amount = fields.Float(string="Transferencia POS")
    cxc_transfer_amount = fields.Float(string="Transferencia CxC")
    total_transfer_collected = fields.Float(string="Total Transferencia")
    other_amount = fields.Float(string="Otros POS")
    cxc_other_amount = fields.Float(string="Otros CxC")
    total_other_collected = fields.Float(string="Total Otros")
    cxc_total_amount = fields.Float(string="Total CxC")
    total_sales = fields.Float(string="Total Recibido")

    pos_name = fields.Char(string="Punto de Venta")
    session_id = fields.Many2one('pos.session', string="Sesión POS")
    pos_config_id = fields.Many2one('pos.config', string="Punto de Venta")
    cashier_id = fields.Many2one('res.users', string="Cajero")

    # Campos display para evitar mostrar 0.00 en filas cabecera
    order_count_display = fields.Char(string="Cant. Órdenes", compute='_compute_display_fields', store=False)
    cxc_receipt_count_display = fields.Char(string="Recibos CxC", compute='_compute_display_fields', store=False)
    cash_amount_display = fields.Char(string="Efectivo POS", compute='_compute_display_fields', store=False)
    driver_liquidation_amount_display = fields.Char(string="Liquidación Chofer", compute='_compute_display_fields', store=False)
    cxc_cash_amount_display = fields.Char(string="Efectivo CxC", compute='_compute_display_fields', store=False)
    total_cash_collected_display = fields.Char(string="Total Efectivo Cobrado", compute='_compute_display_fields', store=False)
    cash_counted_display = fields.Char(string="Efectivo Contado", compute='_compute_display_fields', store=False)
    cash_difference_display = fields.Char(string="Diferencia Efectivo", compute='_compute_display_fields', store=False)
    card_amount_display = fields.Char(string="Tarjeta POS", compute='_compute_display_fields', store=False)
    cxc_card_amount_display = fields.Char(string="Tarjeta CxC", compute='_compute_display_fields', store=False)
    total_card_collected_display = fields.Char(string="Total Tarjeta", compute='_compute_display_fields', store=False)
    transfer_amount_display = fields.Char(string="Transferencia POS", compute='_compute_display_fields', store=False)
    cxc_transfer_amount_display = fields.Char(string="Transferencia CxC", compute='_compute_display_fields', store=False)
    total_transfer_collected_display = fields.Char(string="Total Transferencia", compute='_compute_display_fields', store=False)
    other_amount_display = fields.Char(string="Otros POS", compute='_compute_display_fields', store=False)
    cxc_other_amount_display = fields.Char(string="Otros CxC", compute='_compute_display_fields', store=False)
    total_other_collected_display = fields.Char(string="Total Otros", compute='_compute_display_fields', store=False)
    cxc_total_amount_display = fields.Char(string="Total CxC", compute='_compute_display_fields', store=False)
    total_sales_display = fields.Char(string="Total Recibido", compute='_compute_display_fields', store=False)

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
        'order_count', 'cxc_receipt_count',
        'cash_amount', 'driver_liquidation_amount', 'cxc_cash_amount', 'total_cash_collected',
        'cash_counted', 'cash_difference',
        'card_amount', 'cxc_card_amount', 'total_card_collected',
        'transfer_amount', 'cxc_transfer_amount', 'total_transfer_collected',
        'other_amount', 'cxc_other_amount', 'total_other_collected',
        'cxc_total_amount', 'total_sales'
    )
    def _compute_display_fields(self):
        for rec in self:
            if rec.is_group:
                rec.order_count_display = ''
                rec.cxc_receipt_count_display = ''
                rec.cash_amount_display = ''
                rec.driver_liquidation_amount_display = ''
                rec.cxc_cash_amount_display = ''
                rec.total_cash_collected_display = ''
                rec.cash_counted_display = ''
                rec.cash_difference_display = ''
                rec.card_amount_display = ''
                rec.cxc_card_amount_display = ''
                rec.total_card_collected_display = ''
                rec.transfer_amount_display = ''
                rec.cxc_transfer_amount_display = ''
                rec.total_transfer_collected_display = ''
                rec.other_amount_display = ''
                rec.cxc_other_amount_display = ''
                rec.total_other_collected_display = ''
                rec.cxc_total_amount_display = ''
                rec.total_sales_display = ''
            else:
                rec.order_count_display = str(rec.order_count or 0)
                rec.cxc_receipt_count_display = str(rec.cxc_receipt_count or 0)
                rec.cash_amount_display = f"{rec.cash_amount:,.2f}"
                rec.driver_liquidation_amount_display = f"{rec.driver_liquidation_amount:,.2f}"
                rec.cxc_cash_amount_display = f"{rec.cxc_cash_amount:,.2f}"
                rec.total_cash_collected_display = f"{rec.total_cash_collected:,.2f}"

                if rec.has_cash_counted or rec.is_subtotal:
                    rec.cash_counted_display = f"{rec.cash_counted:,.2f}"
                    rec.cash_difference_display = f"{rec.cash_difference:,.2f}"
                else:
                    rec.cash_counted_display = ''
                    rec.cash_difference_display = ''

                rec.card_amount_display = f"{rec.card_amount:,.2f}"
                rec.cxc_card_amount_display = f"{rec.cxc_card_amount:,.2f}"
                rec.total_card_collected_display = f"{rec.total_card_collected:,.2f}"
                rec.transfer_amount_display = f"{rec.transfer_amount:,.2f}"
                rec.cxc_transfer_amount_display = f"{rec.cxc_transfer_amount:,.2f}"
                rec.total_transfer_collected_display = f"{rec.total_transfer_collected:,.2f}"
                rec.other_amount_display = f"{rec.other_amount:,.2f}"
                rec.cxc_other_amount_display = f"{rec.cxc_other_amount:,.2f}"
                rec.total_other_collected_display = f"{rec.total_other_collected:,.2f}"
                rec.cxc_total_amount_display = f"{rec.cxc_total_amount:,.2f}"
                rec.total_sales_display = f"{rec.total_sales:,.2f}"
