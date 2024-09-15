#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pypdf
import pypdf.annotations

import reportlab.pdfgen.canvas

import math
import argparse
import sys


# PaperSizes are in pts, which are .35 mm

# In[2]:


infilename = "/home/tbogue/Documents/Spells.pdf"
outfilename = None
page_number_margin = 35
binder_folio = True

if len(sys.argv) > 0:
    argparser = argparse.ArgumentParser(description="Converts a pdf file into a bindable format, combining pages together and reordering, as well as adding page numbers")
    argparser.add_argument("infilename", help="input pdf file to parse")
    argparser.add_argument("outfilename", default=None, help="output pdf file to parse.  defaults to infilname-book.pdf", nargs="?")
    argparser.add_argument("--page-margin", dest="page_margin", default=35, type=int, help="margin from bottom or edge of page to put the page number.  Measured in points")
    argparser.add_argument("--skip-binder-folio", dest="skip_binder", default=False, action="store_true")
    args = argparser.parse_args()
    infilename = args.infilename
    outfilename = args.outfilename
    page_number_margin = args.page_margin
    binder_folio = not args.skip_binder
    print(f"processing {infilename} {'' if outfilename == None else 'to ' + outfilename + ' '}with margin {page_number_margin} and {'with' if binder_folio else 'without'} a binder folio")


# In[ ]:


def get_page_numbers(mediabox, left_page, right_page):
    tmpfile="tmprl.pdf"
    canvas = reportlab.pdfgen.canvas.Canvas(tmpfile, pagesize=(mediabox[2], mediabox[3]))
    # make sure inputs are strings
    left_page = f"{left_page}"
    right_page = f"{right_page}"
    if left_page != "0":
        canvas.drawString(page_number_margin, page_number_margin, left_page)
    if right_page != "0":
        canvas.drawString(mediabox[2] - canvas.stringWidth(right_page) - page_number_margin, page_number_margin, right_page)
    canvas.showPage()
    canvas.save()
    reader = pypdf.PdfReader(tmpfile)
    return reader.pages[0]


# In[ ]:


def make_sheet(writer, page1, page2, page3, page4, pageNumbers=None):
    width = page1.mediabox[2]
    height = page1.mediabox[3]
    sheet1 = writer.add_blank_page(width = width * 2, height = height)
    #page1.mediabox = page2.mediabox = page3.mediabox = page4.mediabox = sheet1.mediabox
    sheet1.merge_transformed_page(
        page1,
        pypdf.Transformation().translate(width,0)
    )
    sheet1.merge_transformed_page(
        page4,
        pypdf.Transformation().translate(0, 0)
    )
    sheet2 = writer.add_blank_page(width = width * 2, height = height)
    sheet2.merge_transformed_page(
        page2,
        pypdf.Transformation().translate(0, 0)
    )
    sheet2.merge_transformed_page(
        page3,
        pypdf.Transformation().translate(width, 0)
    )
    sheet1_numbers = get_page_numbers(sheet1.mediabox, pageNumbers[3], pageNumbers[0])
    sheet2_numbers = get_page_numbers(sheet2.mediabox, pageNumbers[1], pageNumbers[2])
    sheet1.merge_page(sheet1_numbers)
    sheet2.merge_page(sheet2_numbers)


# In[ ]:


def signature_plan(num_pages, binder_folio=True):
    sheets_per_signature = 8
    # reserve 4 pages for binding
    total_pages = num_pages + 4
    # add extra pages to make an integral number of sheets
    num_sheets = math.ceil(total_pages / 4)
    total_pages = 4 * num_sheets
    num_signatures = math.ceil(num_sheets / sheets_per_signature)
    extra_pages = total_pages - num_pages
    pairs_of_extra_pages = math.ceil(extra_pages / 2)
    extra_front_pages = 2 * math.ceil(pairs_of_extra_pages / 2)
    extra_back_pages = extra_pages - extra_front_pages
    all_pages = [0] * extra_front_pages + list(range(1, num_pages + 1)) + [0] * extra_back_pages
    current_page = 0
    signatures = []
    for signatureNum in range(0, num_signatures):
        signature = []
        starting_page = current_page
        pages_left = total_pages - current_page
        sheets_left = int(pages_left / 4)
        signatures_left = num_signatures - signatureNum
        num_sheets_in_signature = math.ceil(sheets_left / signatures_left)
        ending_page = current_page + num_sheets_in_signature * 4 - 1
        for sheet_num in range(0, num_sheets_in_signature):
            sheet = [ 
                starting_page + sheet_num * 2,
                starting_page + sheet_num * 2 + 1,
                ending_page - sheet_num * 2 - 1,
                ending_page - sheet_num * 2
            ]
            signature.append(sheet)
        signatures.append(signature)
        current_page = ending_page + 1
    return({"page_list":all_pages, "signatures":signatures})


# In[ ]:


# returns a blank page if page_id is 0 or the page otherwise
def get_page(reader, page_id, reverse=False):
    if page_id == 0:
        width = reader.pages[0].mediabox[2]
        height = reader.pages[1].mediabox[3]
        return pypdf._page.PageObject.create_blank_page(height=height, width=width)
    else:
#        page_editor = pypdf.PdfWriter()
#        page = reader.pages[page_id - 1]
#        page_editor.add_page(page)
#        width = page.mediabox[2]
#        rect = (5,5,23,20)
#        if (page_id % 2 == 0) != reverse :
#            rect = (width-rect[2], 5, width-rect[0], 20)
#        page_num_annotation = pypdf.annotations.FreeText(
#            rect=rect,
#            text=f'{page_id}'
#        )
#       page_editor.add_annotation(page_number=0, annotation=page_num_annotation)
#       page_editor.write("tmp.pdf")
        return reader.pages[page_id - 1]


# In[ ]:


def convert_pdf(infilename, outfileName=None):
    if outfileName == None:
        outfileName = infilename[0:-4] + "-book.pdf"
    reader = pypdf.PdfReader(infilename)
    writer = pypdf.PdfWriter()
    plan = signature_plan(len(reader.pages), binder_folio)
    signatures = plan['signatures']
    page_list = plan['page_list']
    for signature in signatures:
        for sheet in signature:            
            page_nums = [
                page_list[sheet[0]],
                page_list[sheet[1]],
                page_list[sheet[2]],
                page_list[sheet[3]]
            ]
            make_sheet(
                writer, 
                get_page(reader, page_nums[0], True),
                get_page(reader, page_nums[1], True),
                get_page(reader, page_nums[2], True),
                get_page(reader, page_nums[3], True),
                page_nums
            )
    writer.write(outfileName)


# In[ ]:


convert_pdf(infilename)


# In[ ]:




