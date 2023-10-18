from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate
from reportlab.graphics import shapes

import Dao
import Service
from Dao import *
from Dao import CustomerStatementDao
from app import app


def tobeGenerateCustomerStatementFile(eodDate, startEodStatus):
    global successno, errorno, start, end, batchSize, temp, totalCount

    try:

        totalStmtCount = Dao.totalStmtGenerationCount(startEodStatus)

        successno = 0
        errorno = 0
        start = 0
        end = 0
        batchSize = 50
        totalCount = 0

        if batchSize > totalStmtCount:
            end = totalStmtCount
        else:
            end = batchSize

        while(totalCount < totalStmtCount):

            df2 = Dao.getStatementIdsForStatementFileCreation(startEodStatus, start, end)

            for ind in df2.index:
                errorcount = errorno
                successcount = successno
                statementid = df2['stmtid'][ind]
                successno, errorno = genarateCustomerStatement(statementid, eodDate, errorcount, successcount,
                                                               startEodStatus, start, end)

    except Exception as err:
        app.logger.error('Error in Customer Statement Generate controller {}'.format(str(err)))

    return successno, errorno


def genarateCustomerStatement(statementid, eodDate, errorcount, successcount, startEodStatus, start, end):
    try:
        # get data from db
        df1 = CustomerStatementDao.getdataFromMainQuery(statementid)
        # df1 = CustomerStatementDao.getStatementIdsForStatementFileCreation(startEodStatus, start, end)
        filename, filepath = Service.genarateCustomerStatement(df1["accountno"].values[0], eodDate, statementid)

        # get billing address and name
        name, address1, address2, address3 = CustomerStatementDao.getBillingAddress(df1["cardcategorycode"].values[0],
                                                                                    df1["cardno"].values[0])

        df2 = CustomerStatementDao.getDatafromSecondQuery(df1["accountno"].values[0], df1["starteodid"].values[0],
                                                          df1["endeodid"].values[0])

        # define page size and create a SimpleDocTemplate  object
        bottom_margin = 0.5 * inch
        top_margin = 0.4 * inch
        left_margin = 0.5 * inch
        right_margin = 0.5 * inch
        doc = SimpleDocTemplate(filename=filename, pagesize=letter, bottomMargin=bottom_margin,
                                topMargin=top_margin, leftMargin=left_margin, rightMargin=right_margin)
        # row headers
        row_x = 0
        row_y = 0
        row_width = 7.5 * inch
        row_height = 20
        # row = shapes.Rect(row_x, row_y, row_width, row_height, fillColor=colors.white, strokeColor=colors.white)

        # create the content for the template
        elements = []

        # title
        customer_name = shapes.Drawing(row_width, 10)
        address_row_1 = shapes.Drawing(row_width, 10)
        address_row_2 = shapes.Drawing(row_width, 10)
        address_row_3 = shapes.Drawing(row_width, 8)

        if address1 is None:
            name = ''
        else:
            name = name
        customer = shapes.String(0, 8, name, fontName="Helvetica-Bold", fontSize=8, fillColor=colors.black)
        customer_name.add(customer)
        elements.append(customer_name)

        if address1 is None:
            address1 = ''
        else:
            address1 = address1
        addr1 = shapes.String(0, 8, address1, fontName="Helvetica", fontSize=8, fillColor=colors.black)
        address_row_1.add(addr1)
        elements.append(address_row_1)

        if address2 is None:
            address2 = ''
        else:
            address2 = address2
        addr2 = shapes.String(0, 8, address2, fontName="Helvetica", fontSize=8, fillColor=colors.black)
        address_row_2.add(addr2)
        elements.append(address_row_2)

        if address3 is None:
            address3 = ''
        else:
            address3 = address3
        addr3 = shapes.String(0, 8, address3, fontName="Helvetica", fontSize=8, fillColor=colors.black)
        address_row_3.add(addr3)
        elements.append(address_row_3)

        # horizontal line
        horizontal_line = shapes.Drawing(row_width, 5)
        row_1 = shapes.Rect(row_x, row_y, row_width, 1, fillColor=colors.black, strokeColor=colors.black)
        horizontal_line.add(row_1)
        elements.append(horizontal_line)

        ## page header
        header_row_1 = shapes.Drawing(row_width, 10)
        string_cardnumber = shapes.String(0, 0, 'Card Number', fontName="Helvetica-Bold", fontSize=8)
        # header_row_1.add(row)
        header_row_1.add(string_cardnumber)

        string_date = shapes.String(1.5 * inch, 0, 'Statement Date', fontName="Helvetica-Bold", fontSize=8)
        header_row_1.add(string_date)

        string_date = shapes.String(3 * inch, 0, 'Total Outstanding', fontName="Helvetica-Bold", fontSize=8)
        header_row_1.add(string_date)

        string_date = shapes.String(4.5 * inch, 0, 'Credit limit', fontName="Helvetica-Bold", fontSize=8)
        header_row_1.add(string_date)

        string_date = shapes.String(5.5 * inch, 0, 'Due Date', fontName="Helvetica-Bold", fontSize=8)
        header_row_1.add(string_date)

        string_date = shapes.String(6.5 * inch, 0, 'Minimum Payment', fontName="Helvetica-Bold", fontSize=8)
        header_row_1.add(string_date)

        elements.append(header_row_1)

        # row 2
        header_row_2 = shapes.Drawing(row_width, 15)
        cardno = card_number_masking(str(df1['cardno'].values[0]))
        parameter_cardnumber = shapes.String(0, 0, cardno, fontName="Helvetica", fontSize=8)
        # header_row_1.add(row)
        header_row_2.add(parameter_cardnumber)

        parameter_date = shapes.String(1.5 * inch, 0, str(df1["statementenddate"].values[0])[:10], fontName="Helvetica",
                                       fontSize=8)
        header_row_2.add(parameter_date)

        # $P{ClosingBalance}<0 ? " CR" : " "
        if df1["closingbalance"].values[0] < 0:
            addon = 'CR'
        else:
            addon = ' '
        parameter_date = shapes.String(3 * inch, 0, str(df1["closingbalance"].values[0]) + ' ' + addon,
                                       fontName="Helvetica", fontSize=8)
        header_row_2.add(parameter_date)

        parameter_date = shapes.String(4.5 * inch, 0, str(df1["creditlimit"].values[0]), fontName="Helvetica",
                                       fontSize=8)
        header_row_2.add(parameter_date)

        parameter_date = shapes.String(5.5 * inch, 0, str(df1["duedate"].values[0])[:10], fontName="Helvetica",
                                       fontSize=8)
        header_row_2.add(parameter_date)

        parameter_date = shapes.String(6.5 * inch, 0, str(df1["minamount"].values[0]), fontName="Helvetica", fontSize=8)
        header_row_2.add(parameter_date)

        elements.append(header_row_2)
        elements.append(horizontal_line)

        # row 3
        header_row_3 = shapes.Drawing(row_width, 10)
        string_cardnumber = shapes.String(0, 0, 'Page Number', fontName="Helvetica-Bold", fontSize=8)
        # header_row_3.add(row)
        header_row_3.add(string_cardnumber)

        string_date = shapes.String(1.5 * inch, 0, 'Opening Balance', fontName="Helvetica-Bold", fontSize=8)
        header_row_3.add(string_date)

        string_date = shapes.String(3.5 * inch, 0, 'Debits', fontName="Helvetica-Bold", fontSize=8)
        header_row_3.add(string_date)

        string_date = shapes.String(5 * inch, 0, 'Credits', fontName="Helvetica-Bold", fontSize=8)
        header_row_3.add(string_date)

        string_date = shapes.String(6.5 * inch, 0, 'Total Outstanding', fontName="Helvetica-Bold", fontSize=8)
        header_row_3.add(string_date)

        elements.append(header_row_3)

        # header row 4
        header_row_4 = shapes.Drawing(row_width, 15)
        parameter_cardnumber = shapes.String(0, 0, 'Page 1 of 1', fontName="Helvetica", fontSize=8)
        # header_row_1.add(row)
        header_row_4.add(parameter_cardnumber)

        if df1["openingbalance"].values[0] < 0:
            opening_balance = -1 * df1["openingbalance"].values[0]
            addon = 'CR'
        else:
            opening_balance = df1["openingbalance"].values[0]
            addon = ' '
            # $P{OpenBalance}<0 ? " CR" : " "
        parameter_date = shapes.String(1.5 * inch, 0, str(opening_balance) + ' ' + addon, fontName="Helvetica",
                                       fontSize=8)
        header_row_4.add(parameter_date)

        outstanding_ttl = df1["purchases"].values[0] + df1["cashadvance"].values[0] + df1["interest"].values[0] + \
                          df1["dradjustment"].values[0] + df1["charges"].values[0]
        parameter_date = shapes.String(3.5 * inch, 0, str(outstanding_ttl), fontName="Helvetica", fontSize=8)
        header_row_4.add(parameter_date)

        parameter_date = shapes.String(5 * inch, 0, str(df1["payment"].values[0]), fontName="Helvetica", fontSize=8)
        header_row_4.add(parameter_date)

        if df1["closingbalance"].values[0] < 0:
            closing_balance = -1 * df1["closingbalance"].values[0]
            addon = 'CR'
        else:
            closing_balance = df1["closingbalance"].values[0]
            addon = ' '
        parameter_date = shapes.String(6.5 * inch, 0, str(closing_balance) + ' ' + addon, fontName="Helvetica",
                                       fontSize=8)
        header_row_4.add(parameter_date)

        elements.append(header_row_4)
        elements.append(horizontal_line)
        # end page header

        # column header
        column_row = shapes.Drawing(row_width, 15)
        string_billing_date = shapes.String(0, 0, 'Billing Date', fontName="Helvetica-Bold", fontSize=8)
        column_row.add(string_billing_date)

        string_txn_date = shapes.String(1 * inch, 0, 'Txn Date', fontName="Helvetica-Bold", fontSize=8)
        column_row.add(string_txn_date)

        string_description = shapes.String(2 * inch, 0, 'Transaction Description', fontName="Helvetica-Bold",
                                           fontSize=8)
        column_row.add(string_description)

        string_transaction_amount = shapes.String(6.5 * inch, 0, 'Transaction Amount', fontName="Helvetica-Bold",
                                                  fontSize=8)
        column_row.add(string_transaction_amount)
        elements.append(column_row)
        elements.append(horizontal_line)

        # detail

        # get data from query 2
        for ind in df2.index:
            # row 1
            detail_row1 = shapes.Drawing(row_width, 15)
            string_billing_date = shapes.String(0, 0, str(df2['settlementdate'][ind])[6:10], fontName="Helvetica",
                                                fontSize=8)
            detail_row1.add(string_billing_date)

            string_txn_date = shapes.String(1 * inch, 0, str(df2['transactiondate'][ind])[6:10], fontName="Helvetica",
                                            fontSize=8)
            detail_row1.add(string_txn_date)

            string_description = shapes.String(2 * inch, 0, str(df2['transactiondescription'][ind]),
                                               fontName="Helvetica",
                                               fontSize=8)
            detail_row1.add(string_description)

            if df2['crdr'][ind] == 'CR':
                addon = " CR"
            string_transaction_amount = shapes.String(6.5 * inch, 0, str(df2['transactionamount'][ind]) + addon,
                                                      fontName="Helvetica",
                                                      fontSize=8)
            detail_row1.add(string_transaction_amount)
            elements.append(detail_row1)

            # row 2
            detail_row2 = shapes.Drawing(row_width, 15)
            string_billing_date = shapes.String(0, 0, str(df2['settlementdate'][ind])[:10], fontName="Helvetica",
                                                fontSize=8)
            detail_row2.add(string_billing_date)

            string_txn_date = shapes.String(1 * inch, 0, str(df2['transactiondate'][ind])[:10], fontName="Helvetica",
                                            fontSize=8)
            detail_row2.add(string_txn_date)

            string_description = shapes.String(2 * inch, 0, 'CASH ADVANCE FEE', fontName="Helvetica",
                                               fontSize=8)
            detail_row2.add(string_description)

            string_transaction_amount = shapes.String(6.5 * inch, 0, str(df2['cashadvancefee'][ind]) + addon,
                                                      fontName="Helvetica",
                                                      fontSize=8)
            detail_row2.add(string_transaction_amount)
            # elements.append(detail_row2)

        # row 3
        cardno = card_number_masking(str(df2['cardnumber'][ind]))
        detail_row3 = shapes.Drawing(row_width, 15)
        string_txn_date = shapes.String(2 * inch, 0, cardno, fontName="Helvetica-Bold", fontSize=8)
        detail_row3.add(string_txn_date)

        name_on_card = "--" if df2['nameoncard'][ind] is None else df2['nameoncard'][ind]
        string_description = shapes.String(3.0 * inch, 0, name_on_card, fontName="Helvetica-Bold",
                                           fontSize=8)
        detail_row3.add(string_description)

        string_transaction_amount = shapes.String(4.5 * inch, 0, 'SUB TOTAL', fontName="Helvetica",
                                                  fontSize=8)
        detail_row3.add(string_transaction_amount)

        string_debits = shapes.String(5.5 * inch, 0, '-DEBITS', fontName="Helvetica",
                                      fontSize=8)
        detail_row3.add(string_debits)

        # $V{total card debits}==null ? 0.00 : ($V{total card debits}  - $V{total_refunds})
        string_ttl_debits = shapes.String(6.5 * inch, 0, 'please edit', fontName="Helvetica",
                                          fontSize=8)
        detail_row3.add(string_ttl_debits)
        elements.append(detail_row3)
        # end

        #### sub report two
        # get data to sub report two
        df3 = CustomerStatementDao.get_data_for_subreport_two(df1["cardno"].values[0])
        sub_report_two(df3, row_width, elements, str(df1["statementenddate"].values[0])[6:10], df2)

        #### sub report one
        df4 = CustomerStatementDao.get_data_for_subreport_one(df1["cardno"].values[0])
        sub_report_one(df4, elements, row_width, df2)

        # account group footer1
        # account footer row 1
        account_footer_row1 = shapes.Drawing(row_width, 15)
        string_txn_date = shapes.String(0 * inch, 0, 'CashBack Rewards', fontName="Helvetica-Bold", fontSize=8)
        account_footer_row1.add(string_txn_date)
        elements.append(account_footer_row1)

        # row 2
        account_footer_row2 = shapes.Drawing(row_width, 15)
        string_txn_date = shapes.String(0 * inch, 0, 'Opening Balance', fontName="Helvetica", fontSize=8)
        account_footer_row2.add(string_txn_date)

        string_cashback = shapes.String(1.5 * inch, 0, 'CashBack for this Statement', fontName="Helvetica",
                                        fontSize=8)
        account_footer_row2.add(string_cashback)

        string_redeemed = shapes.String(4 * inch, 0, 'Redeemed', fontName="Helvetica", fontSize=8)
        account_footer_row2.add(string_redeemed)

        string_expired = shapes.String(5 * inch, 0, 'Expired/Adjusted', fontName="Helvetica", fontSize=8)
        account_footer_row2.add(string_expired)

        string_ttl_cashback = shapes.String(6.5 * inch, 0, 'Total CashBack', fontName="Helvetica", fontSize=8)
        account_footer_row2.add(string_ttl_cashback)
        elements.append(account_footer_row2)

        # row 3
        space = '            '
        account_footer_row3 = shapes.Drawing(row_width, 15)
        # $F{OPENNINGCASHBACK} == null ? 0 : $F{OPENNINGCASHBACK}
        cashback = 0.00 if df2['openningcashback'][ind] is None else df2['openningcashback'][ind]
        string_txn_date = shapes.String(0.25 * inch, 0, str(cashback) + space + '     +', fontName="Helvetica",
                                        fontSize=8)
        account_footer_row3.add(string_txn_date)

        # $F{CASHBACKAMOUNTWITHOUTADJ}
        string_cashback = shapes.String(1.75 * inch, 0,
                                        str(df2['cashbackamountwithoutadj'][ind]) + space + '          -',
                                        fontName="Helvetica",
                                        fontSize=8)
        account_footer_row3.add(string_cashback)

        string_redeemed = shapes.String(4 * inch, 0,
                                        str(df2['redeemtotalcb'][ind]) + space + '      -',
                                        fontName="Helvetica",
                                        fontSize=8)
        account_footer_row3.add(string_redeemed)

        # $F{CBEXPAMOUNTWITHADJ}
        string_expired = shapes.String(5.25 * inch, 0, str(df2['cbexpamountwithadj'][ind]) + space + '          =',
                                       fontName="Helvetica",
                                       fontSize=8)
        account_footer_row3.add(string_expired)

        # $F{AVLCBAMOUNT}avlcbamount
        string_ttl_cashback = shapes.String(6.75 * inch, 0, str(df2['avlcbamount'][ind]), fontName="Helvetica",
                                            fontSize=8)
        account_footer_row3.add(string_ttl_cashback)
        elements.append(account_footer_row3)

        # row 4
        account_footer_row4 = shapes.Drawing(row_width, 30)
        string_credited = shapes.String(0 * inch, 15, 'Total CashBack to be', fontName="Helvetica", fontSize=8)
        string_txn_date = shapes.String(0.4 * inch, 0, 'credited', fontName="Helvetica", fontSize=8)
        account_footer_row4.add(string_txn_date)
        account_footer_row4.add(string_credited)

        # $F{REDEEMABLECASHBACK}
        string_redeemablecashback = shapes.String(1.5 * inch, 10, ":   " + str(df2['redeemablecashback'][ind]),
                                                  fontName="Helvetica")
        account_footer_row4.add(string_redeemablecashback)
        elements.append(account_footer_row4)

        # row 5
        account_footer_row5 = shapes.Drawing(row_width, 15)
        string_cashback = shapes.String(0.3 * inch, 0, 'CashBack Credit Account', fontName="Helvetica-Bold", fontSize=8)
        account_footer_row5.add(string_cashback)
        elements.append(account_footer_row5)

        # row 6
        account_footer_row6 = shapes.Drawing(row_width, 15)
        # df2['cbaccountname'][ind] == null ? "--" : df2['cbaccountname'][ind]
        acc_holder = "--" if df2['cbaccountname'][ind] is None else df2['cbaccountname'][ind]
        string_acc_holder = shapes.String(0.3 * inch, 0, 'Account Holder :  ' + acc_holder, fontName="Helvetica-Bold",
                                          fontSize=8)
        account_footer_row6.add(string_acc_holder)
        elements.append(account_footer_row6)

        # row 7
        account_footer_row7 = shapes.Drawing(row_width, 15)
        acc_no = "--" if df2['cbaccountno'][ind] is None else df2['cbaccountno'][ind]
        string_acc_holder = shapes.String(0.3 * inch, 0, 'Account No :  ' + acc_no, fontName="Helvetica-Bold",
                                          fontSize=8)
        account_footer_row7.add(string_acc_holder)
        elements.append(account_footer_row7)

        # row 8
        account_footer_row8 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.3 * inch, 0,
                                          'Total CashBack amount indicated above will be credited within 30 days. Conditions apply.',
                                          fontName="Helvetica-Bold", fontSize=8)
        account_footer_row8.add(string_acc_holder)
        elements.append(account_footer_row8)
        # end cashback

        elements.append(horizontal_line)

        # footer
        # row 1
        footer_row1 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.0 * inch, 0, 'Cardholder Name', fontName="Helvetica-Bold", fontSize=8)
        footer_row1.add(string_acc_holder)

        string_outstanding = shapes.String(6.5 * inch, 0, 'Total Outstanding', fontName="Helvetica-Bold", fontSize=8)
        footer_row1.add(string_outstanding)
        elements.append(footer_row1)

        # row 2
        footer_row2 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.0 * inch, 0, name, fontName="Helvetica-Bold", fontSize=8)
        footer_row2.add(string_acc_holder)

        add = "  CR" if df1["closingbalance"].values[0] < 0 else " "
        string_acc_holder = shapes.String(6.5 * inch, 0, str(df1["closingbalance"].values[0]) + add,
                                          fontName="Helvetica", fontSize=8)
        footer_row2.add(string_acc_holder)
        elements.append(footer_row2)

        # row 3
        footer_row3 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.0 * inch, 0, 'Card Number', fontName="Helvetica-Bold", fontSize=8)
        footer_row3.add(string_acc_holder)

        string_acc_holder = shapes.String(6.5 * inch, 0, 'Credit Limit', fontName="Helvetica-Bold", fontSize=8)
        footer_row3.add(string_acc_holder)
        elements.append(footer_row3)

        # row 4
        footer_row4 = shapes.Drawing(row_width, 15)
        cardno = card_number_masking(str(df1['cardno'].values[0]))
        string_acc_holder = shapes.String(0.0 * inch, 0, cardno, fontName="Helvetica", fontSize=8)
        footer_row4.add(string_acc_holder)

        string_acc_holder = shapes.String(6.5 * inch, 0, str(df1['creditlimit'].values[0]), fontName="Helvetica",
                                          fontSize=8)
        footer_row4.add(string_acc_holder)
        elements.append(footer_row4)

        # row 5
        footer_row5 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.0 * inch, 0, 'Due Date', fontName="Helvetica-Bold", fontSize=8)
        footer_row5.add(string_acc_holder)

        string_acc_holder = shapes.String(6.5 * inch, 0, 'Minimum Payment', fontName="Helvetica-Bold", fontSize=8)
        footer_row5.add(string_acc_holder)
        elements.append(footer_row5)

        # row 6
        footer_row6 = shapes.Drawing(row_width, 15)
        string_acc_holder = shapes.String(0.0 * inch, 0, str(df1["duedate"].values[0])[:10], fontName="Helvetica",
                                          fontSize=8)
        footer_row6.add(string_acc_holder)

        string_acc_holder = shapes.String(6.5 * inch, 0, str(df1["minamount"].values[0]), fontName="Helvetica",
                                          fontSize=8)
        footer_row6.add(string_acc_holder)
        elements.append(footer_row6)

        # build the template
        doc.build(elements)
        app.logger.info('successfully created ' + filename)
        successcount += 1
        Dao.updateStatus(statementid)

    except Exception as err:
        app.logger.error('Error while generating  Customer Statement PDF  {}'.format(str(err)))
        errorcount += 1
        Dao.updateErrorFileStatus(statementid)

    return successcount, errorcount


def card_number_masking(card_number):
    global masked_cardnumber
    try:
        pattern = PATTERN_CHAR[0] * (END_INDEX - START_INDEX)
        masked_cardnumber = card_number[:START_INDEX] + pattern + card_number[END_INDEX:]

    except Exception as err:
        app.logger.error('Error while masking card number  {}'.format(str(err)))
    return masked_cardnumber


def sub_report_two(df3, row_width, elements, statementenddate, df2):
    try:
        total_fee_r2 = 0
        total_interest_r2 = 0
        # sub report two loop
        for ind in df3.index:
            # row 1
            # print(df3['cardnumber'][ind], df3['interrest'][ind], ind)

            column_row = shapes.Drawing(row_width, 15)
            string_billing_date = shapes.String(0, 0, str(df3['effectdate'][ind])[6:10], fontName="Helvetica",
                                                fontSize=8)
            column_row.add(string_billing_date)

            string_txn_date = shapes.String(1 * inch, 0, str(df3['effectdate'][ind])[6:10], fontName="Helvetica",
                                            fontSize=8)
            column_row.add(string_txn_date)

            string_description = shapes.String(2 * inch, 0, str(df3['description'][ind]).upper(), fontName="Helvetica",
                                               fontSize=8)
            column_row.add(string_description)

            # $F{FEEAMOUNT}==null ? 0.00 : $F{FEEAMOUNT}
            feeamount = 0.00 if df3['feeamount'][ind] is None else df3['feeamount'][ind]
            total_fee_r2 += feeamount
            string_transaction_amount = shapes.String(6.5 * inch, 0, str(feeamount), fontName="Helvetica",
                                                      fontSize=8)
            column_row.add(string_transaction_amount)
            elements.append(column_row)

            # row two
            column_row = shapes.Drawing(row_width, 15)
            string_billing_date = shapes.String(0, 0, statementenddate, fontName="Helvetica", fontSize=8)
            column_row.add(string_billing_date)

            string_txn_date = shapes.String(1 * inch, 0, statementenddate, fontName="Helvetica", fontSize=8)
            column_row.add(string_txn_date)

            string_description = shapes.String(2 * inch, 0, 'INTEREST CHARGE', fontName="Helvetica",
                                               fontSize=8)
            column_row.add(string_description)

            # $F{INTERREST}==null ? 0.00 : $F{INTERREST}
            # interest = 0.00 if df3['interrest'][ind] is None else df3['interrest'][ind]
            if df3['interrest'][ind] is None:
                interest = 0.00
            else:
                interest = df3['interrest'][ind]
            total_interest_r2 += interest
            string_transaction_amount = shapes.String(6.5 * inch, 0, str(interest), fontName="Helvetica",
                                                      fontSize=8)
            column_row.add(string_transaction_amount)
            elements.append(column_row)

        # row 3
        cardno = card_number_masking(str(df3['cardnumber'][ind]))
        detail_row3 = shapes.Drawing(row_width, 15)
        string_txn_date = shapes.String(2 * inch, 0, cardno, fontName="Helvetica-Bold", fontSize=8)
        detail_row3.add(string_txn_date)

        name_on_card = "--" if df2['nameoncard'].values[0] is None else df2['nameoncard'].values[0]
        string_description = shapes.String(3.0 * inch, 0, name_on_card, fontName="Helvetica-Bold",
                                           fontSize=8)
        detail_row3.add(string_description)

        string_transaction_amount = shapes.String(4.5 * inch, 0, 'SUB TOTAL', fontName="Helvetica",
                                                  fontSize=8)
        detail_row3.add(string_transaction_amount)

        string_debits = shapes.String(5.5 * inch, 0, '-DEBITS', fontName="Helvetica",
                                      fontSize=8)
        detail_row3.add(string_debits)

        # ($V{TotalFee}==null && $F{INTERREST} ==null) ? 0.00 :
        # ($F{INTERREST}==null &&$V{TotalFee}!= null) ? $V{TotalFee} :
        # ($V{TotalFee}==null &&$F{INTERREST}!=null) ?$F{INTERREST} :
        # ($F{INTERREST}!=null &&$V{TotalFee}!=null) ?$V{TotalFee}+$F{INTERREST}.doubleValue():0.00
        if total_fee_r2 is None and total_interest_r2 is None:
            sub_ttl_r2 = 0.00
        elif total_interest_r2 is None and total_fee_r2 is not None:
            sub_ttl_r2 = total_fee_r2
        elif total_fee_r2 is None and total_interest_r2 is not None:
            sub_ttl_r2 = total_interest_r2
        elif total_fee_r2 is not None and total_interest_r2 is not None:
            sub_ttl_r2 = float(total_fee_r2 + total_interest_r2)
        else:
            sub_ttl_r2 = 0.00

        string_ttl_debits = shapes.String(6.5 * inch, 0, str(sub_ttl_r2), fontName="Helvetica",
                                          fontSize=8)
        detail_row3.add(string_ttl_debits)
        elements.append(detail_row3)

    except Exception as err:
        app.logger.error('Error while generating sub report two  {}'.format(str(err)))


def sub_report_one(df4, elements, row_width, df2):
    try:
        totaladj_reportone = 0
        loop = 0
        for ind in df4.index:
            loop = 1
            column_row = shapes.Drawing(row_width, 15)
            string_billing_date = shapes.String(0, 0, str(df4['adjustdate'][ind])[6:10], fontName="Helvetica",
                                                fontSize=8)
            column_row.add(string_billing_date)

            string_txn_date = shapes.String(1 * inch, 0, str(df4['adjustdate'][ind])[6:10], fontName="Helvetica",
                                            fontSize=8)
            column_row.add(string_txn_date)

            # $F{REMARKS}==null ? "" :$F{REMARKS}.toUpperCase()
            if df4['remarks'][ind] is None:
                remark = ''
            else:
                remark = df4['remarks'][ind].upper()
            string_description = shapes.String(2 * inch, 0, remark, fontName="Helvetica",
                                               fontSize=8)
            column_row.add(string_description)

            # $F{CRDR}.equals("CR")?"CR":" "
            if df4['crdr'][ind] == 'CR':
                addon = " CR"
            string_transaction_amount = shapes.String(6.5 * inch, 0, str(df4['amount'][ind]) + ' ' + addon,
                                                      fontName="Helvetica",
                                                      fontSize=8)
            totaladj_reportone += df4['amount'][ind]
            column_row.add(string_transaction_amount)
            elements.append(column_row)

        # row 3
        if loop > 0:
            cardno = card_number_masking(str(df2['cardnumber'].values[0]))
            detail_row3 = shapes.Drawing(row_width, 15)
            string_txn_date = shapes.String(2 * inch, 0, cardno, fontName="Helvetica-Bold", fontSize=8)
            detail_row3.add(string_txn_date)

            name_on_card = "--" if df2['nameoncard'].values[0] is None else df2['nameoncard'].values[0]
            string_description = shapes.String(3.0 * inch, 0, name_on_card, fontName="Helvetica-Bold",
                                               fontSize=8)
            detail_row3.add(string_description)

            string_transaction_amount = shapes.String(4.5 * inch, 0, 'SUB TOTAL', fontName="Helvetica",
                                                      fontSize=8)
            detail_row3.add(string_transaction_amount)

            string_debits = shapes.String(5.5 * inch, 0, '-DEBITS', fontName="Helvetica",
                                          fontSize=8)
            detail_row3.add(string_debits)

            string_ttl_debits = shapes.String(6.5 * inch, 0, str(totaladj_reportone), fontName="Helvetica",
                                              fontSize=8)
            detail_row3.add(string_ttl_debits)
            elements.append(detail_row3)


    except Exception as err:
        app.logger.error('Error while generating sub report one  {}'.format(str(err)))
