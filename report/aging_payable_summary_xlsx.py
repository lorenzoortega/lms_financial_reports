from odoo import models


class AgingPayableSummaryXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.aging_payable_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Balance por Antigüedad Resumido Proveedores XLSX'

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
            sheet = workbook.add_worksheet('Resumen Prov.')
            report_data = wizard._get_report_data()
            company = wizard.env.company

            row = 0
            sheet.write(row, 0, 'Balance por Antigüedad Resumido (Proveedores)', title_format)
            row += 1
            sheet.write(row, 0, f'Empresa: {company.name}', normal_format)
            row += 1
            sheet.write(row, 0, f'Rango: {report_data["date_from"]} - {report_data["date_to"]}', normal_format)
            row += 2

            headers = ['Proveedor', 'Balance Pendiente', 'No Vencida', '1-30', '31-60', '61-90', '90+']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            for line in report_data['lines']:
                sheet.write(row, 0, line['vendor_name'], normal_format)
                sheet.write(row, 1, line['balance_pending'], number_format)
                sheet.write(row, 2, line['not_due'], number_format)
                sheet.write(row, 3, line['bucket_1_30'], number_format)
                sheet.write(row, 4, line['bucket_31_60'], number_format)
                sheet.write(row, 5, line['bucket_61_90'], number_format)
                sheet.write(row, 6, line['bucket_90_plus'], number_format)
                row += 1

            sheet.write(row, 0, 'TOTAL GENERAL', subtotal_format)
            sheet.write(row, 1, report_data['totals']['balance_pending'], subtotal_format)
            sheet.write(row, 2, report_data['totals']['not_due'], subtotal_format)
            sheet.write(row, 3, report_data['totals']['bucket_1_30'], subtotal_format)
            sheet.write(row, 4, report_data['totals']['bucket_31_60'], subtotal_format)
            sheet.write(row, 5, report_data['totals']['bucket_61_90'], subtotal_format)
            sheet.write(row, 6, report_data['totals']['bucket_90_plus'], subtotal_format)

            sheet.set_column(0, 0, 30)
            sheet.set_column(1, 6, 16)