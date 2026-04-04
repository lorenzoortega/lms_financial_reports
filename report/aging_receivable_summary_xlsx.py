from odoo import models, _


class AgingReceivableSummaryXlsx(models.AbstractModel):
    _name = 'report.lms_financial_reports.aging_receivable_summary_xlsx'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'Balance por Antigüedad Resumido XLSX'

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
            sheet = workbook.add_worksheet(_('Antigüedad Resumen'))
            report_data = wizard._get_report_data()

            row = 0
            sheet.write(row, 0, 'Balance por Antigüedad Resumido', title_format)
            row += 1
            sheet.write(row, 0, f"Fecha Inicio: {report_data['date_from']}")
            row += 1
            sheet.write(row, 0, f"Fecha Fin: {report_data['date_to']}")
            row += 2

            headers = ['Cliente', 'Balance Pendiente', 'No Vencida', '1-30', '31-60', '61-90', '90+']
            for col, header in enumerate(headers):
                sheet.write(row, col, header, header_format)
            row += 1

            for line in report_data['lines']:
                sheet.write(row, 0, line['customer_name'], normal_format)
                sheet.write_number(row, 1, line['balance_pending'], number_format)
                sheet.write_number(row, 2, line['not_due'], number_format)
                sheet.write_number(row, 3, line['bucket_1_30'], number_format)
                sheet.write_number(row, 4, line['bucket_31_60'], number_format)
                sheet.write_number(row, 5, line['bucket_61_90'], number_format)
                sheet.write_number(row, 6, line['bucket_90_plus'], number_format)
                row += 1

            sheet.write(row, 0, 'TOTAL GENERAL', group_format)
            sheet.write_number(row, 1, report_data['totals']['balance_pending'], subtotal_format)
            sheet.write_number(row, 2, report_data['totals']['not_due'], subtotal_format)
            sheet.write_number(row, 3, report_data['totals']['bucket_1_30'], subtotal_format)
            sheet.write_number(row, 4, report_data['totals']['bucket_31_60'], subtotal_format)
            sheet.write_number(row, 5, report_data['totals']['bucket_61_90'], subtotal_format)
            sheet.write_number(row, 6, report_data['totals']['bucket_90_plus'], subtotal_format)

            sheet.set_column(0, 0, 30)
            sheet.set_column(1, 6, 16)
