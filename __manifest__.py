{
    'name': 'LMS Financial Reports',
    'version': '1.5',
    'summary': 'Reportes Financieros Profesionales LMS',
    'author': 'LMS',
    'depends': [
        'account',
        'point_of_sale',   # 🔥 IMPORTANTE
        'report_xlsx',
    ],
    'data': [

        # Seguridad
        'security/security.xml',
        'security/ir.model.access.csv',

        # =========================
        # ESTADO DE RESULTADOS
        # =========================
        'views/income_statement_wizard_view.xml',
        'views/income_statement_line_views.xml',
        'report/income_statement_pdf.xml',
        'report/income_statement_xlsx.xml',

        # =========================
        # BALANZA DE COMPROBACIÓN
        # =========================
        'views/trial_balance_wizard_view.xml',
        'views/trial_balance_line_views.xml',
        'report/trial_balance_pdf.xml',
        'report/trial_balance_xlsx.xml',

        # =========================
        # POS REPORT
        # =========================
        'views/pos_report_wizard_view.xml',
        'views/pos_report_line_views.xml',
        'report/pos_report_pdf.xml',
        'report/pos_report_xlsx.xml',

        # =========================
        # POS DAILY REPORT
        # =========================
        'views/pos_daily_report_line_views.xml',
        'views/pos_daily_report_wizard_view.xml',
        'report/pos_daily_report_pdf.xml',
        'report/pos_daily_report_xlsx.xml',

        # =========================
        # ACTA DE CIERRE CAJA POS
        # =========================
        'views/pos_cash_closing_act_line_views.xml',
        'views/pos_cash_closing_act_wizard_view.xml',
        'report/pos_cash_closing_act_pdf.xml',
        'report/pos_cash_closing_act_report.xml',


        # =========================
        # CONTABILIDAD - CUENTA POR COBRAR
        # =========================
        'views/aging_receivable_report_wizard_view.xml',
	'views/aging_receivable_report_line_views.xml',
	'views/aging_receivable_summary_wizard_view.xml',
	'views/aging_receivable_summary_line_views.xml',
	'report/aging_receivable_report_pdf.xml',
	'report/aging_receivable_summary_pdf.xml',
	'report/aging_receivable_report_xlsx.xml',
	'report/aging_receivable_summary_xlsx.xml',


	'views/aging_wizard_actions.xml',  # 👈 ESTE NUEVO

        # =========================
        # CONTABILIDAD - CUENTA POR PAGAR
        # =========================
        'views/aging_payable_report_wizard_view.xml',
	'views/aging_payable_summary_wizard_view.xml',
	'views/aging_payable_report_line_view.xml',
	'views/aging_payable_summary_line_view.xml',
	'report/aging_payable_xlsx_actions.xml',
	'report/aging_payable_report_pdf.xml',
	'report/aging_payable_summary_pdf.xml',
	
        # =========================
        # MENÚ (SIEMPRE AL FINAL)
        # =========================
        'views/financial_reports_menu.xml',
    ],
    'installable': True,
    'application': True,
}