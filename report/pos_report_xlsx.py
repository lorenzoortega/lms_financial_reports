from odoo import models


class PosReportXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.pos_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Reporte por POS XLSX'

    def generate_xlsx_report(self, workbook, data, wizard):
        groups = wizard._get_pos_report_data()
        company = wizard.env.company

        sheet_name = "Reporte POS"
        sheet = workbook.add_worksheet(sheet_name[:31])

        title_format = workbook.add_format({
            'bold': True,
            'font_size': 14,
        })

        header_format = workbook.add_format({
            'bold': True,
            'align': 'center',
            'border': 1,
        })

        group_format = workbook.add_format({
            'bold': True,
            'bg_color': '#EAEAEA',
        })

        subtotal_format = workbook.add_format({
            'bold': True,
            'bg_color': '#F5F5F5',
            'num_format': '#,##0.00',
        })

        number_format = workbook.add_format({
            'num_format': '#,##0.00',
            'align': 'right',
        })

        row = 0
        sheet.write(row, 0, "Reporte por POS", title_format)
        row += 1
        sheet.write(row, 0, f"Empresa: {company.name}")
        row += 1
        sheet.write(row, 0, f"Rango: {wizard.date_from} - {wizard.date_to}")
        row += 1
        if wizard.pos_config_id:
            sheet.write(row, 0, f"Punto de Venta: {wizard.pos_config_id.display_name}")
            row += 1
        row += 1

        headers = [
            "Fecha",
            "Punto de Venta",
            "Sesión",
            "Estado",
            "Cajero",
            "Orden POS",
            "Factura",
            "NCF",
            "Cliente",
            "Método de Pago",
            "Monto",
        ]

        for group in groups:
            sheet.write(row, 0, group['header'], group_format)
            row += 1

            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            for line in group['lines']:
                sheet.write(row, 0, str(line['date'] or ''))
                sheet.write(row, 1, line['pos_name'])
                sheet.write(row, 2, line['session_name'])
                sheet.write(row, 3, line['session_state'])
                sheet.write(row, 4, line['cashier_name'])
                sheet.write(row, 5, line['order_name'])
                sheet.write(row, 6, line['invoice_name'])
                sheet.write(row, 7, line['ncf_number'])
                sheet.write(row, 8, line['customer_name'])
                sheet.write(row, 9, line['payment_method_name'])
                sheet.write(row, 10, line['amount'], number_format)
                row += 1

            sheet.write(row, 0, "SUBTOTAL SESIÓN", group_format)
            sheet.write(row, 10, group['total_amount'], subtotal_format)
            row += 2

        sheet.set_column(0, 0, 22)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 12)
        sheet.set_column(4, 4, 18)
        sheet.set_column(5, 6, 18)
        sheet.set_column(7, 8, 20)
        sheet.set_column(9, 9, 18)
        sheet.set_column(10, 10, 14)
