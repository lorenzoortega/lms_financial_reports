from odoo import models


class PosDailyReportXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.pos_daily_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte Ventas POS Día XLSX'

    def generate_xlsx_report(self, workbook, data, wizard):
        report_data = wizard._get_report_data()
        company = wizard.env.company

        sheet = workbook.add_worksheet("Ventas POS Día")

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
        })
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14
        })
        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right'
        })
        bold_number_format = workbook.add_format({
            'bold': True,
            'num_format': '#,##0.00',
            'align': 'right'
        })
        bold_format = workbook.add_format({'bold': True})
        group_format = workbook.add_format({
            'bold': True,
            'bg_color': '#EAEAEA'
        })
        subtotal_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F5F5F5'
        })

        row = 0
        sheet.write(row, 0, "REPORTE VENTAS POS DIA", title_format)
        row += 1
        sheet.write(row, 0, f"Empresa: {company.name}")
        row += 1
        sheet.write(row, 0, f"Fecha: {wizard.date}")
        row += 1
        if wizard.pos_config_id:
            sheet.write(row, 0, f"Punto de Venta: {wizard.pos_config_id.display_name}")
            row += 1
        row += 1

        headers = [
            "Fecha / POS",
            "Estado",
            "Cajero",
            "Cant. Órdenes POS",
            "Recibos CxC",
            "Sesión",
            "Rango Sesión",
            "Efectivo POS",
            "Efectivo CxC",
            "Total Efectivo",
            "Liq. Chofer",
            "Efectivo Contado",
            "Dif. Efectivo",
            "Tarjeta POS",
            "Tarjeta CxC",
            "Total Tarjeta",
            "Transferencia POS",
            "Transferencia CxC",
            "Total Transferencia",
            "Total CxC",
            "TOTAL RECIBIDO",
        ]

        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        row += 1

        for group in report_data['pos_groups']:
            sheet.write(row, 0, group['pos_name'], group_format)
            row += 1

            for line in group['sessions']:
                sheet.write(row, 0, str(line['date'] or ''))
                sheet.write(row, 1, line['session_state'])
                sheet.write(row, 2, line['cashier_name'])
                sheet.write(row, 3, line['order_count'])
                sheet.write(row, 4, line['cxc_receipt_count'])
                sheet.write(row, 5, line['session_name'])
                sheet.write(row, 6, line['session_range'])
                sheet.write(row, 7, line['cash_amount'], number_format)
                sheet.write(row, 8, line['cxc_cash_amount'], number_format)
                sheet.write(row, 9, line['total_cash_collected'], number_format)
                sheet.write(row, 10, line['driver_liquidation_amount'], number_format)

                if line.get('has_cash_counted'):
                    sheet.write(row, 11, line['cash_counted'], number_format)
                    sheet.write(row, 12, line['cash_difference'], number_format)
                else:
                    sheet.write(row, 11, '')
                    sheet.write(row, 12, '')

                sheet.write(row, 13, line['card_amount'], number_format)
                sheet.write(row, 14, line['cxc_card_amount'], number_format)
                sheet.write(row, 15, line['total_card_collected'], number_format)
                sheet.write(row, 16, line['transfer_amount'], number_format)
                sheet.write(row, 17, line['cxc_transfer_amount'], number_format)
                sheet.write(row, 18, line['total_transfer_collected'], number_format)
                sheet.write(row, 19, line['cxc_total_amount'], number_format)
                sheet.write(row, 20, line['total_sales'], number_format)
                row += 1

            subtotal = group.get('subtotal') or {}
            sheet.write(row, 0, "SUBTOTAL %s" % group['pos_name'], subtotal_format)
            sheet.write(row, 3, subtotal.get('order_count', 0))
            sheet.write(row, 4, subtotal.get('cxc_receipt_count', 0))
            sheet.write(row, 7, subtotal.get('cash_amount', 0.0), bold_number_format)
            sheet.write(row, 8, subtotal.get('cxc_cash_amount', 0.0), bold_number_format)
            sheet.write(row, 9, subtotal.get('total_cash_collected', 0.0), bold_number_format)
            sheet.write(row, 10, subtotal.get('driver_liquidation_amount', 0.0), bold_number_format)
            sheet.write(row, 11, subtotal.get('cash_counted', 0.0), bold_number_format)
            sheet.write(row, 12, subtotal.get('cash_difference', 0.0), bold_number_format)
            sheet.write(row, 13, subtotal.get('card_amount', 0.0), bold_number_format)
            sheet.write(row, 14, subtotal.get('cxc_card_amount', 0.0), bold_number_format)
            sheet.write(row, 15, subtotal.get('total_card_collected', 0.0), bold_number_format)
            sheet.write(row, 16, subtotal.get('transfer_amount', 0.0), bold_number_format)
            sheet.write(row, 17, subtotal.get('cxc_transfer_amount', 0.0), bold_number_format)
            sheet.write(row, 18, subtotal.get('total_transfer_collected', 0.0), bold_number_format)
            sheet.write(row, 19, subtotal.get('cxc_total_amount', 0.0), bold_number_format)
            sheet.write(row, 20, subtotal.get('total_sales', 0.0), bold_number_format)
            row += 1

        row += 1
        totals = report_data['totals']
        sheet.write(row, 0, "TOTAL RECIBIDO POS DIA", bold_format)
        sheet.write(row, 3, totals['order_count'])
        sheet.write(row, 4, totals['cxc_receipt_count'])
        sheet.write(row, 7, totals['cash_amount'], bold_number_format)
        sheet.write(row, 8, totals['cxc_cash_amount'], bold_number_format)
        sheet.write(row, 9, totals['total_cash_collected'], bold_number_format)
        sheet.write(row, 10, totals['driver_liquidation_amount'], bold_number_format)
        sheet.write(row, 11, totals['cash_counted'], bold_number_format)
        sheet.write(row, 12, totals['cash_difference'], bold_number_format)
        sheet.write(row, 13, totals['card_amount'], bold_number_format)
        sheet.write(row, 14, totals['cxc_card_amount'], bold_number_format)
        sheet.write(row, 15, totals['total_card_collected'], bold_number_format)
        sheet.write(row, 16, totals['transfer_amount'], bold_number_format)
        sheet.write(row, 17, totals['cxc_transfer_amount'], bold_number_format)
        sheet.write(row, 18, totals['total_transfer_collected'], bold_number_format)
        sheet.write(row, 19, totals['cxc_total_amount'], bold_number_format)
        sheet.write(row, 20, totals['total_sales'], bold_number_format)

        sheet.set_column(0, 0, 16)
        sheet.set_column(1, 1, 12)
        sheet.set_column(2, 2, 18)
        sheet.set_column(3, 4, 16)
        sheet.set_column(5, 5, 16)
        sheet.set_column(6, 6, 38)
        sheet.set_column(7, 20, 18)
