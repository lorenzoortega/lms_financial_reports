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
            'bg_color': '#F2F2F2'
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
            "Fecha", "RANGO SESIÓN", "Sesión", "Estado", "Cajero", "Cant. Órdenes",
            "Efectivo", "Liquidación Chofer", "Total Efectivo Cobrado",
            "Tarjeta", "Transferencia", "ITBIS", "Total Ventas"
        ]
        for col, header in enumerate(headers):
            sheet.write(row, col, header, header_format)
        row += 1

        for group in report_data['pos_groups']:
            sheet.write(row, 0, group['pos_name'], group_format)
            row += 1

            for line in group['sessions']:
                sheet.write(row, 0, str(line['date'] or ''))
                sheet.write(row, 1, line['session_range'])
                sheet.write(row, 2, line['session_name'])
                sheet.write(row, 3, line['session_state'])
                sheet.write(row, 4, line['cashier_name'])
                sheet.write(row, 5, line['order_count'])
                sheet.write(row, 6, line['cash_amount'], number_format)
                sheet.write(row, 7, line['cash_diff'], number_format)
                sheet.write(row, 8, line['cash_real'], number_format)
                sheet.write(row, 9, line['card_amount'], number_format)
                sheet.write(row, 10, line['transfer_amount'], number_format)
                sheet.write(row, 11, line['tax_amount'], number_format)
                sheet.write(row, 12, line['total_amount'], number_format)
                row += 1

            sheet.write(row, 0, f"SUBTOTAL {group['pos_name']}", subtotal_format)
            sheet.write(row, 6, group['subtotal']['cash_amount'], bold_number_format)
            sheet.write(row, 7, group['subtotal']['cash_diff'], bold_number_format)
            sheet.write(row, 8, group['subtotal']['cash_real'], bold_number_format)
            sheet.write(row, 9, group['subtotal']['card_amount'], bold_number_format)
            sheet.write(row, 10, group['subtotal']['transfer_amount'], bold_number_format)
            sheet.write(row, 11, group['subtotal']['tax_amount'], bold_number_format)
            sheet.write(row, 12, group['subtotal']['total_amount'], bold_number_format)
            row += 2

        sheet.write(row, 0, "TOTAL VENTAS POS DIA", bold_format)
        sheet.write(row, 6, report_data['totals']['cash_amount'], bold_number_format)
        sheet.write(row, 7, report_data['totals']['cash_diff'], bold_number_format)
        sheet.write(row, 8, report_data['totals']['cash_real'], bold_number_format)
        sheet.write(row, 9, report_data['totals']['card_amount'], bold_number_format)
        sheet.write(row, 10, report_data['totals']['transfer_amount'], bold_number_format)
        sheet.write(row, 11, report_data['totals']['tax_amount'], bold_number_format)
        sheet.write(row, 12, report_data['totals']['total_amount'], bold_number_format)

        sheet.set_column(0, 0, 12)
        sheet.set_column(1, 1, 38)
        sheet.set_column(2, 4, 14)
        sheet.set_column(5, 5, 14)
        sheet.set_column(6, 8, 22)
        sheet.set_column(9, 12, 14)
