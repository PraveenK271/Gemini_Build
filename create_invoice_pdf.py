import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageTemplate, Frame
from reportlab.lib.enums import TA_RIGHT, TA_CENTER, TA_LEFT
from reportlab.lib.colors import black, gray, white
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from num2words import num2words

# Constants
PAGE_WIDTH, PAGE_HEIGHT = A4
MARGIN = 15 * mm
CONTENT_WIDTH = PAGE_WIDTH - 2 * MARGIN
LOGO_HEIGHT = 15 * mm
 
# Styles
styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name='RightAlign', alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='CenterAlign', alignment=TA_CENTER))
styles.add(ParagraphStyle(name='LeftAlign', alignment=TA_LEFT))
styles.add(ParagraphStyle(name='InvoiceTitle', fontSize=12, alignment=TA_CENTER, spaceAfter=6))
styles.add(ParagraphStyle(name='CompanyInfo', fontSize=9, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='CustomerInfo', fontSize=9, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='TableHeader', fontSize=8, alignment=TA_CENTER, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='TableCell', fontSize=8, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='TableCellRight', fontSize=8, alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='TotalsLabel', fontSize=9, alignment=TA_RIGHT, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle(name='TotalsValue', fontSize=9, alignment=TA_RIGHT))
styles.add(ParagraphStyle(name='BankDetails', fontSize=8, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='Terms', fontSize=8, alignment=TA_LEFT))
styles.add(ParagraphStyle(name='AmountInWords', fontSize=8, alignment=TA_LEFT, leading=10))

def format_number(value):
    try:
        return f"{value:,.2f}"
    except:
        return "0.00"

def create_invoice(filename: str, data: dict):
    def header_footer(canvas, doc):
        canvas.saveState()
        canvas.setFont('Helvetica-Bold', 9)
        canvas.drawCentredString(PAGE_WIDTH/2.0, PAGE_HEIGHT - 20, "TAX INVOICE")
        canvas.setFont('Helvetica', 8)
        canvas.drawRightString(PAGE_WIDTH - MARGIN, 10, f"Page {doc.page}")
        canvas.restoreState()

    doc = SimpleDocTemplate(filename, pagesize=A4,
                            leftMargin=MARGIN, rightMargin=MARGIN,
                            topMargin=MARGIN, bottomMargin=MARGIN)
    frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height - 20, id='normal')
    template = PageTemplate(id='invoice', frames=frame, onPage=header_footer)
    doc.addPageTemplates([template])

    story = []

    # --- Company Header with Seller + Invoice Info in one row
    seller_para = Paragraph(
        f"<b>SELLER</b><br/><b>{data['company_name']}</b><br/>{data['company_address']}<br/>"
        f"Mobile: {data['company_mobile']}<br/>GSTIN: {data['company_gstin']}",
        styles['CustomerInfo']
    )

    invoice_info = Table([
        [Paragraph(f"<b>Invoice No:</b> {data['invoice_no']}", styles['TableCellRight'])],
        [Paragraph(f"<b>Invoice Date:</b> {data['invoice_date']}", styles['TableCellRight'])],
    ], colWidths=[CONTENT_WIDTH * 0.4])
    invoice_info.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'TOP')
    ]))

    seller_invoice_table = Table([[seller_para, invoice_info]],
                                  colWidths=[CONTENT_WIDTH * 0.6, CONTENT_WIDTH * 0.4])
    story.append(seller_invoice_table)
    story.append(Spacer(1, 5*mm))

    # --- Bill To Section stays below Seller
    bill_to = Paragraph(
        f"<b>BILL TO</b><br/><b>{data['customer_name']}</b><br/>{data['customer_address']}<br/>"
        f"Mobile: {data['customer_mobile']}<br/>GSTIN: {data['customer_gstin']}",
        styles['CustomerInfo']
    )
    story.append(bill_to)
    story.append(Spacer(1, 5*mm))

    # --- Items Table with only vertical borders
    headers = ['S.No', 'Description', 'HSN', 'Qty', 'Rate', 'Amount']
    data_tbl = [[Paragraph(h, styles['TableHeader']) for h in headers]]

    for idx, it in enumerate(data['items'], start=1):
        data_tbl.append([
            Paragraph(str(idx), styles['TableCell']),
            Paragraph(it['description'], styles['TableCell']),
            Paragraph(it['hsn'], styles['TableCell']),
            Paragraph(str(it['qty']), styles['TableCell']),
            Paragraph(format_number(it['rate']), styles['TableCellRight']),
            Paragraph(format_number(it['amount']), styles['TableCellRight']),
        ])

    while len(data_tbl) < 23:
        data_tbl.append([Paragraph("", styles['TableCell']) for _ in range(len(headers))])

    col_widths = [
        CONTENT_WIDTH * 0.06,
        CONTENT_WIDTH * 0.40,
        CONTENT_WIDTH * 0.10,
        CONTENT_WIDTH * 0.10,
        CONTENT_WIDTH * 0.16,
        CONTENT_WIDTH * 0.18
    ]
    tbl = Table(data_tbl, colWidths=col_widths)
    tbl.setStyle(TableStyle([
        ('LINEBEFORE', (1,0), (-1, -1), 0.5, black),  # Vertical lines only between columns
        ('BACKGROUND', (0,0), (-1,0), gray),
        ('TEXTCOLOR', (0,0), (-1,0), white)
    ]))
    story.append(tbl)
    story.append(Spacer(1, 6*mm))


    # Combined Amount in Words + Totals
    t = data['totals']
    amount_words = num2words(t['total_amount'], lang='en_IN').title() + " Only"
    left_part = Paragraph(f"<b>Amount in Words:</b><br/>{amount_words}", styles['AmountInWords'])

    totals_rows = [
        [Paragraph('Taxable Amount', styles['TotalsLabel']), Paragraph(format_number(t['taxable_amount']), styles['TotalsValue'])]
    ]
    if t.get('igst_percent', 0) > 0:
        totals_rows.append([Paragraph(f"IGST @{t['igst_percent']}%", styles['TotalsLabel']), Paragraph(format_number(t['igst_amount']), styles['TotalsValue'])])
    else:
        totals_rows.append([Paragraph(f"CGST @{t['cgst_percent']}%", styles['TotalsLabel']), Paragraph(format_number(t['cgst_amount']), styles['TotalsValue'])])
        totals_rows.append([Paragraph(f"SGST @{t['sgst_percent']}%", styles['TotalsLabel']), Paragraph(format_number(t['sgst_amount']), styles['TotalsValue'])])
    totals_rows.append([Paragraph('<b>Total Amount</b>', styles['TotalsLabel']), Paragraph(format_number(t['total_amount']), styles['TotalsValue'])])

    totals_table = Table(totals_rows, colWidths=[CONTENT_WIDTH * 0.35, CONTENT_WIDTH * 0.15])
    totals_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, black),
        ('LINEABOVE', (0,-1), (1,-1), 0.5, black),
        ('LINEBELOW', (0,-1), (1,-1), 0.5, black)
    ]))

    combined_table = Table([
        [left_part, totals_table]
    ], colWidths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.5])
    combined_table.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.5, black),
        ('LINEBEFORE', (1,0), (1,0), 0.5, black)
    ]))

    story.append(combined_table)
    story.append(Spacer(1, 6*mm))

    # Bank Details + Signatory Side-by-Side
    bank = data
    bank_para = Paragraph(
        f"<b>Bank Details</b><br/>Name: {bank['bank_name_beneficiary']}<br/>"
        f"A/c No: {bank['bank_account_no']}<br/>IFSC: {bank['bank_ifsc']}<br/>Branch: {bank['bank_name_branch']}",
        styles['BankDetails']
    )
    signatory = Paragraph(
        f"for {data['company_name']}<br/><br/><br/><b>Authorised Signatory</b>",
        styles['RightAlign']
    )

    bank_sign_table = Table([[bank_para, signatory]], colWidths=[CONTENT_WIDTH * 0.5, CONTENT_WIDTH * 0.5])
    story.append(bank_sign_table)
    story.append(Spacer(1, 6*mm))

    # Terms
    story.append(Paragraph(
        f"<b>Terms & Conditions</b><br/>1. {bank['terms_1']}<br/>2. {bank['terms_2']}",
        styles['Terms']
    ))
    story.append(Spacer(1, 5*mm))

    # E & O.E at bottom right
    story.append(Paragraph("E. & O.E.", styles['RightAlign']))

    # Add footer note
    if 'footer_note' in data and data['footer_note']:
        story.append(Spacer(1, 5 * mm))
        story.append(Paragraph(data['footer_note'], styles['CenterAlign']))

    # Build PDF
    doc.build(story)

    

