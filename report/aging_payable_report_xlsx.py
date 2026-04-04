from odoo import models


class AgingPayableReportXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.aging_payable_report_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Balance por Antigüedad Proveedores XLSX'

    def generate_xlsx_report(self, workbook, data, wizards):
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

        normal_format = workbook.add_format({})

        for wizard in wizards:
            sheet = workbook.add_worksheet('Antig. Proveedores')
            report_data = wizard._get_report_data()
            company = wizard.env.company

            row = 0
            sheet.write(row, 0, 'Balance por Antigüedad (Proveedores)', title_format)
            row += 1
            sheet.write(row, 0, f'Empresa: {company.name}', normal_format)
            row += 1
            sheet.write(row, 0, f'Rango: {report_data["date_from"]} - {report_data["date_to"]}', normal_format)
            row += 2

            headers = [
                'Proveedor',
                'Factura',
                'Vencimiento',
                'Balance Pendiente',
                'Días Vencidos',
                'No Vencida',
                '1-30',
                '31-60',
                '61-90',
                '90+',
            ]

            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            for group in report_data['vendor_groups']:
                sheet.write(row, 0, group['vendor_name'], group_format)
                for col in range(1, 10):
                    sheet.write(row, col, '', group_format)
                row += 1

                for line in group['lines']:
                    sheet.write(row, 0, line['vendor_name'], normal_format)
                    sheet.write(row, 1, line['invoice_name'], normal_format)
                    sheet.write(row, 2, str(line['due_date'] or ''), normal_format)
                    sheet.write(row, 3, line['balance_pending'], number_format)
                    sheet.write(row, 4, line['days_overdue'], normal_format)
                    sheet.write(row, 5, line['not_due'], number_format)
                    sheet.write(row, 6, line['bucket_1_30'], number_format)
                    sheet.write(row, 7, line['bucket_31_60'], number_format)
                    sheet.write(row, 8, line['bucket_61_90'], number_format)
                    sheet.write(row, 9, line['bucket_90_plus'], number_format)
                    row += 1

                sheet.write(row, 0, 'SUBTOTAL %s' % group['vendor_name'], group_format)
                sheet.write(row, 1, '', group_format)
                sheet.write(row, 2, '', group_format)
                sheet.write(row, 3, group['subtotal']['balance_pending'], subtotal_format)
                sheet.write(row, 4, '', group_format)
                sheet.write(row, 5, group['subtotal']['not_due'], subtotal_format)
                sheet.write(row, 6, group['subtotal']['bucket_1_30'], subtotal_format)
                sheet.write(row, 7, group['subtotal']['bucket_31_60'], subtotal_format)
                sheet.write(row, 8, group['subtotal']['bucket_61_90'], subtotal_format)
                sheet.write(row, 9, group['subtotal']['bucket_90_plus'], subtotal_format)
                row += 1

            sheet.write(row, 0, 'TOTAL GENERAL', subtotal_format)
            sheet.write(row, 1, '', subtotal_format)
            sheet.write(row, 2, '', subtotal_format)
            sheet.write(row, 3, report_data['totals']['balance_pending'], subtotal_format)
            sheet.write(row, 4, '', subtotal_format)
            sheet.write(row, 5, report_data['totals']['not_due'], subtotal_format)
            sheet.write(row, 6, report_data['totals']['bucket_1_30'], subtotal_format)
            sheet.write(row, 7, report_data['totals']['bucket_31_60'], subtotal_format)
            sheet.write(row, 8, report_data['totals']['bucket_61_90'], subtotal_format)
            sheet.write(row, 9, report_data['totals']['bucket_90_plus'], subtotal_format)

            sheet.set_column(0, 0, 30)
            sheet.set_column(1, 1, 18)
            sheet.set_column(2, 2, 14)
            sheet.set_column(3, 9, 14)