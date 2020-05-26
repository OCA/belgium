# -*- coding: utf-8 -*-
#
# Copyright (c) 2014 Acsone SA/NV (http://www.acsone.eu)
# Author: Adrien Peiffer
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from cStringIO import StringIO
import base64
import time
import calendar

import xlwt

try:
    from openerp.addons.account_financial_report_webkit.report.open_invoices \
        import PartnersOpenInvoicesWebkit
except ImportError:
    # module is not installed
    # module 'account_companyweb' depends on module
    # 'account_financial_report_webkit' if the first one
    # is not installed, it's sure that the second one is not
    # We can silently ignore the ImportError since if the module
    # 'account_companyweb' is not installed we don't need
    # to have the account_financial_report_webkit in our addons path
    pass

from odoo import models, fields
from odoo.osv import orm

SUPERUSER_ID = 1


class account_companyweb_report_wizard(models.TransientModel):

    def _getListeOfMonth(self):
        Month = []
        for i in range(1, 13):
            Month.append((str(i).zfill(2), str(i).zfill(2)))
        return Month

    def _getListeOfYear(self):
        Year = []
        for i in range(int(time.strftime('%Y', time.localtime())) - 1,
                       int(time.strftime('%Y', time.localtime())) + 1):
            Year.append((str(i), str(i)))
        return Year

    def _get_account(self):
        company_id = self.env['res.company'] \
            ._company_default_get(object='account.account',
                                  field='company_id')
        accounts = self.env['account.account'].search(
            [('parent_id', '=', False),
             ('company_id', '=', company_id)], limit=1)
        return accounts and accounts[0] or False

    _name = "account.companyweb.report.wizard"
    _description = "Create Report for Companyweb"
    # _columns = {
    #     'chart_account_id': fields.Many2one(
    #         'account.account', 'Chart of Account', required=True,
    #         domain=[('parent_id', '=', False)]),
    #     'month': fields.Selection(_getListeOfMonth, 'Month', required=True),
    #     'year': fields.Selection(_getListeOfYear, 'Year', required=True),
    #     'data': fields.Binary('XLS', readonly=True),
    #     'export_filename': fields.Char('Export CSV Filename', size=128),
    # }
    chart_account_id = fields.Many2one(
        'account.account', 'Chart of Account', required=True,
        domain=[('parent_id', '=', False)])
    month = fields.Selection(_getListeOfMonth, 'Month', required=True)
    year = fields.Selection(_getListeOfYear, 'Year', required=True)
    data = fields.Binary('XLS', readonly=True)
    export_filename = fields.Char('Export CSV Filename', size=128)

    _defaults = {
        'chart_account_id': _get_account,
        'month': lambda *a: time.strftime('%m'),
        'year': lambda *a: time.strftime('%Y'),
    }

    def create_createdSalesDocs(self, ids):
        context = self.env.context
        if context is None:
            context = {}
        this = self.browse(ids)[0]

        wbk = xlwt.Workbook()

        sheet1 = wbk.add_sheet('createdSalesDocs')

        for i in range(0, 12):
            sheet1.col(i).width = 4000

        pos = 0

        sheet1.write(pos, 0, "ORIGINVATNO")
        sheet1.write(pos, 1, "BOOKYEAR")
        sheet1.write(pos, 2, "SALEBOOK")
        sheet1.write(pos, 3, "SALESDOCNO")
        sheet1.write(pos, 4, "DOCTYPE")
        sheet1.write(pos, 5, "DOCDATE")
        sheet1.write(pos, 6, "EXPDATE")
        sheet1.write(pos, 7, "CUSTVATNO")
        sheet1.write(pos, 8, "TOTAMOUNT")
        sheet1.write(pos, 9, "MONTH")
        sheet1.write(pos, 10, "YEAR")
        sheet1.write(pos, 11, "REPORTDATE")

        r = PartnersOpenInvoicesWebkit("name", {})
        account_ids = r.get_all_accounts(
            this.chart_account_id.id, exclude_type=['view'],
            only_type=['receivable'])

        maxDayOfMonth = calendar.monthrange(int(this.year), int(this.month))[1]
        maxDayOfMonth = str(maxDayOfMonth)

        move_line_model = self.env["account.move.line"]

        move_line_ids = move_line_model.search(

            [('account_id.id', 'in', account_ids),
             ('journal_id.type', 'in', ('sale', 'sale_refund')),
             ('date', '>=', this.year + '-' + this.month + '-01'),
             ('date', '<=', this.year + '-' + this.month + '-' + maxDayOfMonth)
             ])

        pos += 1
        for element in move_line_model.browse(move_line_ids):
            sheet1.write(pos, 0, element.company_id.vat)
            sheet1.write(pos, 1, element.period_id.name)
            sheet1.write(pos, 2, element.journal_id.name)
            sheet1.write(pos, 3, element.move_id.name)
            amout = element.debit - element.credit
            if amout < 0:
                sheet1.write(pos, 4, "LC")
            else:
                sheet1.write(pos, 4, "I")
            sheet1.write(pos, 8, amout)
            sheet1.write(pos, 5, element.date)
            sheet1.write(pos, 6, element.date_maturity)
            sheet1.write(pos, 7, element.partner_id.vat)
            sheet1.write(pos, 9, this.month)
            sheet1.write(pos, 10, this.year)
            sheet1.write(pos, 11, time.strftime('%Y-%m-%d', time.localtime()))
            pos += 1

        file_data = StringIO()
        wbk.save(file_data)

        out = base64.encodestring(file_data.getvalue())

        filename = this.chart_account_id.company_id.vat + '_' + this.year + \
        this.month + '.xls'
        self.write(ids,
                   {'data': out,
                    'export_filename': 'CreatedSalesDocs_' + filename})

        return {
            'name': 'Companyweb Report',
            'type': 'ir.actions.act_window',
            'res_model': 'account.companyweb.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }

    def create_openSalesDocs(self, ids):
        context = self.env.context
        if context is None:
            context = {}
        this = self.browse(ids)[0]

        wbk = xlwt.Workbook()
        sheet1 = wbk.add_sheet('openSalesDocs')

        for i in range(0, 14):
            sheet1.col(i).width = 4000

        pos = 0
        sheet1.write(pos, 0, "ORIGINVATNO")
        sheet1.write(pos, 1, "BOOKYEAR")
        sheet1.write(pos, 2, "SALEBOOK")
        sheet1.write(pos, 3, "SALESDOCNO")
        sheet1.write(pos, 4, "DOCTYPE")
        sheet1.write(pos, 5, "DOCDATE")
        sheet1.write(pos, 6, "EXPDATE")
        sheet1.write(pos, 7, "CUSTVATNO")
        sheet1.write(pos, 8, "TOTAMOUNT")
        sheet1.write(pos, 9, "OPENAMOUT")
        sheet1.write(pos, 10, "CUSTACCBAL")
        sheet1.write(pos, 11, "MONTH")
        sheet1.write(pos, 12, "YEAR")
        sheet1.write(pos, 13, "REPORTDATE")

        maxDayOfMonth = calendar.monthrange(int(this.year), int(this.month))[1]
        maxDayOfMonth = str(maxDayOfMonth)

        fy_model = self.pool['account.fiscalyear']
        move_line_model = self.pool['account.move.line']

        # r = PartnersOpenInvoicesWebkit(cr, uid, "name", {})
        r = PartnersOpenInvoicesWebkit("name", {})

        date_until = this.year + '-' + this.month + '-' + maxDayOfMonth
        fy_ids = fy_model.search(
            [('date_start', '<=', date_until),
             ('date_stop', '>=', date_until)])
        if (len(fy_model.browse(fy_ids)) == 0):
            raise orm.except_orm('No fiscal year ' + this.year + ' found', '')
        else:
            fy = fy_model.browse(fy_ids)[0]

        start_period = r.get_first_fiscalyear_period(fy)

        account_ids = r.get_all_accounts(
            this.chart_account_id.id,
            exclude_type=['view'],
            only_type=['receivable'])

        move_line_ids = []
        lines = r._partners_initial_balance_line_ids(account_ids,
                                                     start_period,
                                                     partner_filter=[],
                                                     exclude_reconcile=True,
                                                     force_period_ids=False,
                                                     date_stop=date_until)
        for data in lines:
            move_line_ids.append(data['id'])
        for account_id in account_ids:
            mids = r.get_partners_move_lines_ids(account_id,
                                                 'filter_date',
                                                 start_period.date_start,
                                                 date_until,
                                                 'posted',
                                                 exclude_reconcile=True,
                                                 partner_filter=[]).values()
            for data in mids:
                move_line_ids.extend(data)

        move_line_sales_refund_ids = move_line_model.search(
            [('id', 'in', move_line_ids),
             ('journal_id.type', 'in', ('sale', 'sale_refund'))])

        pos += 1
        for element in move_line_model.browse(
                move_line_sales_refund_ids):
            amount_residual = element.debit - element.credit
            if element.reconcile_id.id or element.reconcile_partial_id.id:
                if element.reconcile_id.id:
                    move_line_ids_reconcile = move_line_model.search(

                        [('reconcile_id', '=', element.reconcile_id.id),
                         ('id', '!=', element.id),
                         ('id', 'in', move_line_ids)],
                        context=context)
                else:
                    partial_id = element.reconcile_partial_id.id
                    move_line_ids_reconcile = move_line_model.search(

                        [('reconcile_partial_id', '=', partial_id),
                         ('id', '!=', element.id),
                         ('id', 'in', move_line_ids)],
                        context=context)
                move_lines = move_line_model.browse(
                    move_line_ids_reconcile, context=context)
                for move_line_reconcile in move_lines:
                    amount_reconcile = move_line_reconcile.credit - \
                    move_line_reconcile.debit
                    amount_residual = amount_residual - amount_reconcile

            partner_credit = 0
            move_line_partner_ids = move_line_model.search(
                [('partner_id', '=', element.partner_id.id),
                 ('id', 'in', move_line_ids)])
            move_lines = move_line_model.browse(
                move_line_partner_ids, context=context)
            for move_line in move_lines:
                partner_credit = partner_credit + (move_line.debit - \
                move_line.credit)
            sheet1.write(pos, 0, element.company_id.vat)
            sheet1.write(pos, 1, element.period_id.name)
            sheet1.write(pos, 2, element.journal_id.name)
            sheet1.write(pos, 3, element.move_id.name)
            amout = element.debit - element.credit
            if amout < 0:
                sheet1.write(pos, 4, "LC")
            else:
                sheet1.write(pos, 4, "I")
            sheet1.write(pos, 5, element.date)
            sheet1.write(pos, 6, element.date_maturity)
            sheet1.write(pos, 7, element.partner_id.vat)
            sheet1.write(pos, 8, amout)
            sheet1.write(pos, 9, amount_residual)
            sheet1.write(pos, 10, partner_credit)
            sheet1.write(pos, 11, this.month)
            sheet1.write(pos, 12, this.year)
            sheet1.write(pos, 13, time.strftime('%Y-%m-%d', time.localtime()))
            pos += 1

        file_data = StringIO()
        wbk.save(file_data)

        out = base64.encodestring(file_data.getvalue())

        filename = 'OpenSalesDocs_' + \
                   this.chart_account_id.company_id.vat + \
                   '_' + \
                   this.year \
                   + \
                   this.month + \
                   '.xls'
        self.write(ids,
                   {'data': out, 'export_filename': filename}, context=context)

        return {
            'name': 'Companyweb Report',
            'type': 'ir.actions.act_window',
            'res_model': 'account.companyweb.report.wizard',
            'view_mode': 'form',
            'view_type': 'form',
            'res_id': this.id,
            'views': [(False, 'form')],
            'target': 'new',
        }
