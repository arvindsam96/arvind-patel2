#! /usr/bin/env python
# -*- coding: utf-8 -*-
# ==============================================================================
#
# Copyright (C) 2010 Nico Schl"omer
#
# This file is part of deutschebank2ofx.
#
# deutschebank2ofx is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# deutschebank2ofx is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deutschebank2ofx.  If not, see <http://www.gnu.org/licenses/>.
#
# ==============================================================================
import datetime
import re
import lxml.etree as etree
# ==============================================================================
def print_ofx( entries ):

    stmtrs = etree.Element( "STMTRS" )

    # add curdef
    currency_element = etree.SubElement(stmtrs, "CURDEF")
    c = etree.SubElement(currency_element, "EUR")

    # bank account from
    bankacctfrom = etree.SubElement(stmtrs, "BANKACCTFROM")

    # add the transaction list
    stmtrs.append( _create_ofx_banktranlist(entries) )

    # ledger balance
    ledgerbal = etree.SubElement(stmtrs, "LEDGERBAL")
    # amount
    balamt = etree.SubElement(ledgerbal, "BALAMT")
    balamt.text = "0.00"

    # date as of
    dtasof = etree.SubElement(ledgerbal, "DTASOF")
    dtasof.text = datetime.date.today().isoformat()

    return etree.tostring( stmtrs,
                           pretty_print = True
                         )
# ==============================================================================
def _create_ofx_banktranlist( entries ):

    banktranlist = etree.Element( "BANKTRANLIST" )

    # start date
    dtstart = etree.SubElement( banktranlist, "DTSTART" )
    dtstart.text = "01-01-1900"

    # end date
    dtend = etree.SubElement( banktranlist, "DTEND" )
    dtend.text = datetime.date.today().isoformat()

    # loop over the transactions
    for entry in entries:
        banktranlist.append( _create_ofx_transaction( entry ) )

    return banktranlist
# ==============================================================================
def _create_ofx_transaction( entry ):

    stmttrn = etree.Element( "STMTTRN" )

    # decide upon the transaction type
    trntype = etree.SubElement( stmttrn, "TRNTYPE" )
    if entry['amount'] > 0:
        trntype.text = "CREDIT"
    else:
        trntype.text = "DEBIT"

    # date posted
    dtposted = etree.SubElement( stmttrn, "DTPOSTED" )
    dtposted.text = entry['date'].strftime('%Y-%m-%d')

    # value date
    if entry['value date'] is not None:
        dtavail = etree.SubElement( stmttrn, "DTAVAIL" )
        dtavail.text = entry['value date'].strftime('%Y-%m-%d')


    # amount of transaction
    trnamt = etree.SubElement( stmttrn, "TRNAMT" )
    trnamt.text = "%.2f" % entry['amount']

    # unique ID
    fitid = etree.SubElement( stmttrn, "FITID" )
    # for now, create the ID of date, %y%m%d, plus the amount
    fitid.text = entry['value date'].strftime('%y%m%d') \
               + "%d" % (abs(entry['amount'])*100)

    # payee
    stmttrn.append( _create_ofx_payee(entry) )

    # bank account to
    stmttrn.append( _create_ofx_bankaccount(entry) )

    # memo
    if entry['message'] is not None:
        memo = etree.SubElement( stmttrn, "MEMO" )
        memo.text = entry['message']

    if entry['currency'] is not None:
        currency = etree.SubElement( stmttrn, "ORIGINALCURRENCY" )
        currency.text = entry['currency']

    return stmttrn
# ==============================================================================
def _create_ofx_payee( entry ):

    payee = etree.Element( "PAYEE" )

    # name
    name = etree.SubElement( payee, "NAME" )
    if entry['payee'] is not None:
        name.text = entry['payee']

    # address 1
    addr1 = etree.SubElement( payee, "ADDR1" )
    if entry['address'] is not None:
        if type(entry['address']) == str:
            addr1.text = entry['address']
        elif type(entry['address']) == tuple:
            for addline in entry['address']:
                addr1.text = addline
        else:
            raise ValueError( "Illegal address field, \""
                              + entry['address'] + "\"."
                            )

    # city
    city = etree.SubElement( payee, "CITY" )
    if entry['city'] is not None:
        city.text = entry['city']

    # state (leave empty)
    state = etree.SubElement( payee, "STATE" )

    # postal code
    postalcode = etree.SubElement( payee, "POSTALCODE" )
    if entry['postal code'] is not None:
        postalcode.text = entry['postal code']

    # optional: country

    # phone
    phone = etree.SubElement( payee, "PHONE" )
    if entry['phone number'] is not None:
        phone.text = entry['phone number']

    return payee
# ==============================================================================
def _create_ofx_bankaccount( entry ):

    tofrom = "BANKACCTTO"

    bankacct = etree.Element( tofrom )

    if entry['account number'] is not None:
        bank_id_parser = re.compile( "(\d\d\d)-.*" )
        res = bank_id_parser.findall( entry['account number'] )
        if len(res) > 0:
            bank_id    = res[0]
            account_id = entry['account number']
        else:
            bank_id    = ""
            account_id = entry['account number']
    elif entry['bic'] is not None and entry['iban'] is not None:
        bank_id    = entry['bic']
        account_id = entry['iban']
    else:
        bank_id    = ""
        account_id = ""

    # TODO: extract first three items off of account number
    # bank ID
    bankid = etree.SubElement( bankacct, "BANKID" )
    bankid.text = bank_id

    # account ID
    acctid = etree.SubElement( bankacct, "ACCTID" )
    acctid.text = account_id

    # account type;
    # one of CHECKING, SAVINGS, MONEYMRKT, CREDITLINE
    accttype = etree.SubElement( bankacct, "ACCTTYPE" )
    accttype.text = "CHECKING"

    return bankacct
# ==============================================================================