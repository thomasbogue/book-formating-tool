#!/usr/bin/env python
# coding: utf-8

# In[1]:


import pypdf
import pypdf.annotations

import reportlab.pdfgen.canvas

import math
import argparse
import sys


# In[2]:


"get_ipython" in vars()


# PaperSizes are in pts, which are .35 mm

# In[3]:


# takes a pypdf.mediabox and returns a page with the left and right page numbers added
# left_page and right_page are the page numbers
# returns the new page with page numbers only
def add_page_numbers(mediabox, left_page, right_page):
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


# In[4]:


# sets up a folio with the given four pages
# pagenumbers should be a list of page numbers for the four pages
def make_folio(writer, page1, page2, page3, page4, pageNumbers):
    width = page1.mediabox[2]
    height = page1.mediabox[3]
    sheet1 = writer.add_blank_page(width = width * 2, height = height)
    sheet1.merge_transformed_page(
        page1,
        pypdf.Transformation().translate(width + inner_margin,0)
    )
    sheet1.merge_transformed_page(
        page4,
        pypdf.Transformation().translate(-inner_margin, 0)
    )
    sheet2 = writer.add_blank_page(width = width * 2 + inner_margin, height = height)
    sheet2.merge_transformed_page(
        page2,
        pypdf.Transformation().translate(-inner_margin, 0)
    )
    sheet2.merge_transformed_page(
        page3,
        pypdf.Transformation().translate(width, 0)
    )
    sheet1_numbers = add_page_numbers(sheet1.mediabox, pageNumbers[3], pageNumbers[0])
    sheet2_numbers = add_page_numbers(sheet2.mediabox, pageNumbers[1], pageNumbers[2])
    sheet1.merge_page(sheet1_numbers)
    sheet2.merge_page(sheet2_numbers)


# In[5]:


# returns a list of lists.  each sublist contains a list of page numbers for that folio
# page number of 0 represents a blank page instead of one from the source document
# if binder_folio is True it will make sure that the first and last two pages are blank 
# so you either have a cover sheet or a page to glue to the cover
def signature_plan(num_pages, binder_folio=True):
    folios_per_signature = 8
    # reserve 4 pages for binding
    total_pages = num_pages + 4
    # add extra pages to make an integral number of folios
    num_sheets = math.ceil(total_pages / 4)
    total_pages = 4 * num_sheets
    num_signatures = math.ceil(num_sheets / folios_per_signature)
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
                all_pages[starting_page + sheet_num * 2],
                all_pages[starting_page + sheet_num * 2 + 1],
                all_pages[ending_page - sheet_num * 2 - 1],
                all_pages[ending_page - sheet_num * 2]
            ]
            signature.append(sheet)
        signatures.append(signature)
        current_page = ending_page + 1
    return(signatures)


# In[6]:


# returns a blank page if page_id is 0 or the page otherwise
def get_page(reader, page_id, reverse=False):
    if page_id == 0:
        width = reader.pages[0].mediabox[2]
        height = reader.pages[1].mediabox[3]
        return pypdf._page.PageObject.create_blank_page(height=height, width=width)
    else:
        return reader.pages[page_id - 1]


# In[7]:


# convert the pdf infilename to a ready-to-print/bind pdf outfilename
# outfilename defaults to infilename-book.pdf
def convert_pdf(infilename, outfileName=None):
    if outfileName == None:
        outfileName = infilename[0:-4] + "-book.pdf"
    reader = pypdf.PdfReader(infilename)
    writer = pypdf.PdfWriter()
    signatures = signature_plan(len(reader.pages), binder_folio)
    for signature in signatures:
        for sheet in signature:            
            page_nums = [
                sheet[0],
                sheet[1],
                sheet[2],
                sheet[3]
            ]
            make_folio(
                writer, 
                get_page(reader, page_nums[0], True),
                get_page(reader, page_nums[1], True),
                get_page(reader, page_nums[2], True),
                get_page(reader, page_nums[3], True),
                page_nums
            )
    writer.write(outfileName)


# In[8]:


if __name__ == "__main__":
    # parse arguments and set defaults
    infilename = "/home/tbogue/Documents/Spells.pdf"
    outfilename = None
    page_number_margin = 35
    binder_folio = True
    inner_margin=3

    if not "get_ipython" in vars():
        argparser = argparse.ArgumentParser(description="Converts a pdf file into a bindable format, combining pages together and reordering, as well as adding page numbers")
        argparser.add_argument("infilename", help="input pdf file to parse")
        argparser.add_argument("outfilename", default=None, help="output pdf file to parse.  defaults to infilname-book.pdf", nargs="?")
        argparser.add_argument("--page-margin", dest="page_margin", default=page_number_margin, type=int, help="margin from bottom or edge of page to put the page number.  Measured in points", nargs=1)
        argparser.add_argument("--skip-binder-folio", dest="skip_binder", default=False, action="store_true")
        argparser.add_argument("--innermargin", dest="innermargin", default=inner_margin, nargs=1)
        args = argparser.parse_args()
        infilename = args.infilename
        outfilename = args.outfilename
        page_number_margin = args.page_margin
        binder_folio = not args.skip_binder
        inner_margin = args.innermargin
    print(f"processing {infilename} {'' if outfilename == None else 'to ' + outfilename + ' '}with page number margin {page_number_margin} and {'with' if binder_folio else 'without'} a binder folio and inner margin of {inner_margin}")
    convert_pdf(infilename)

