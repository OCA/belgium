# -*- encoding: utf-8 -*-
##############################################################################
#
#    Odoo, Open Source Management Solution
#
#    Copyright (c) 2009-2015 Noviat nv/sa (www.noviat.com).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        DELETE FROM ir_model_data
          WHERE module = 'l10n_be_partner'
          AND name in ('rptn_bv', 'rptn_ag', 'rptn_inc')
        """)
