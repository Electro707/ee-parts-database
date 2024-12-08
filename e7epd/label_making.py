import io
import logging
import typing
import os
import re
try:
    import PIL.Image
    # from blabel import label_tools
    # from blabel import LabelWriter
    from PIL import Image
    import barcode as python_barcode
    import cairosvg
    import pypdf
except ImportError as e:
    available = e
    """available is None if printing is available, otherwise it will be the import exception"""
else:
    available = None
# Import my PyPTouch lib to potentially allow for direct printing to a barcode
try:
    import pyPTouch
except ImportError as e:
    direct_printing_failed = e
    """direct_printing_failed is None if printing is available directly to a PTouch Printer, otherwise it will be the import exception"""
else:
    direct_printing_failed = None


class PrinterObject:
    def __init__(self):
        self.printer = pyPTouch.PTouch()
        self.log = logging.getLogger('e7epd.printer')

    def get_availability(self):
        return self.printer.is_printer_available()

    def open(self) -> bool:
        try:
            self.printer.open()
        except pyPTouch.PTouchConnection:
            self.log.info("Unable to connect to a printer")
            return False
        return True

    def close(self):
        self.printer.close()

    def get_current_tape_width(self):
        return self.printer.get_tape_width_px()


def _make_barcode(data: str, **writter_options) -> bytes:
    """Makes a barcode image"""
    constructor = python_barcode.get_barcode_class('code128')
    data = str(data).zfill(constructor.digits)
    # wr = python_barcode.writer.ImageWriter()
    wr = python_barcode.writer.SVGWriter()
    barcode_img = constructor(data, writer=wr)
    return barcode_img.render(writer_options=writter_options)


# def generate_barcodes(ipns: typing.List[str], label_width: float) -> bytes:
#     html_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "label_template.html")
#
#     with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "label_template.css"), 'r') as f:
#         css = f.read()
#
#     css += f"@page {{ height: {label_width}mm;  padding: 0.0mm; }}"
#     css += f"img {{ height:{label_width}mm;  }}"
#
#     records = [{'ipn': i} for i in ipns]
#     for i, r in enumerate(records):
#         # img = _make_barcode(r['ipn'], module_height=label_width, module_width=0.2, text_distance=label_width/2, font_size=label_width, dpi=128, margin_bottom=-0.15*label_width)
#         img = _make_barcode(r['ipn'], module_height=label_width-2, module_width=0.14, text_distance=2, font_size=label_width/2, margin_bottom=0, margin_top=0)
#         img = img.decode()
#         # print(label_width, img.size)
#         r['page_height'] = f'{label_width*2}mm'
#         # r['page_width'] = f"{(img.size[0] * (label_width) / img.size[1]) + 1}mm"
#         r['page_width'] = f"100mm"
#         print(img)
#         r['barcode_data'] = img
#         r['page_id'] = f'page{i}'
#
#         css += f"@page page{i} {{ width: {r['page_width']}; }}"
#
#     css = CSS(string=css)
#
#     label_writer = LabelWriter(item_template_path=html_path, default_stylesheets=(css, ))
#     return label_writer.write_labels(records, target=None)

def generate_barcode(ipn: str, label_width: float) -> bytes:
    """
    Generates a barcode svg
    Args:
        ipn: The part numbers to print
        label_width: The label width, in mm

    Notes:
        This function assumes a 180 DPI printer
    """
    # img = _make_barcode(r['ipn'], module_height=label_width, module_width=0.2, text_distance=label_width/2, font_size=label_width, dpi=128, margin_bottom=-0.15*label_width)
    # img = _make_barcode(r['ipn'], module_height=label_width-3, module_width=0.1411, text_distance=2, font_size=label_width/2, margin_bottom=0, margin_top=0, quiet_zone=0)
    img = _make_barcode(ipn, module_height=label_width-3, module_width=(1/(180/25.4))*1, text_distance=2, font_size=label_width/2, margin_bottom=0, margin_top=0, quiet_zone=0)
    # img = img.decode()

    # thanks chatgpt
    i = img.decode()
    i = re.sub(r'<svg([^>]*)height="([\d\.]+)(mm"[^>]*)>',
               f'<svg\\1height="{label_width}\\3>', i)

    img = i.encode('utf-8')

    return img


def export_barcodes(ipns: typing.List[str], label_width: float, export_path: str):
    """
    Function to give multiple IPN (or other data) to, and exports them as a PDF file containing multiple
    pages for each IPN given

    Args:
        ipns: A list of IPNs (or other data) to convert into barcodes
        label_width: The width (height of looking at it from the front) of the tape
        export_path: The PDF file path to export to
    """
    if not export_path.endswith('.pdf'):
        export_path += '.pdf'

    merger = pypdf.PdfWriter()

    for i in ipns:
        svg = generate_barcode(i, label_width)
        pdf = cairosvg.svg2pdf(bytestring=svg)
        merger.append(io.BytesIO(pdf))
    merger.write(export_path)
    merger.close()


def print_barcodes(ipns: typing.List[str], printer: PrinterObject):
    """
    Blocking function that will print out a barcode per each part number in the list
    Args:
        ipns: A list of part numbers to print out
        printer: The printer object to use
    """
    label_width = printer.get_current_tape_width()
    # assuming 180SPI, for brother printers
    label_width = (label_width / 180) * 25.4

    # end = False
    for i, ip in enumerate(ipns):
        svgs = generate_barcode(ip, label_width)
        # if i == len(ipns)-1:
        #     end = True
        printer.printer.print_svg(svgs, False)
        printer.printer.wait_for_print()


if __name__ == "__main__":
    import cairosvg
    from io import BytesIO
    import sys

    # testing if this file is ran directly
    logging.basicConfig(level=logging.DEBUG)
    w = 12
    data = ['RMCF0603FT10K0', 'abc']
    # data.append("SMALL")
    export_barcodes(data, w, 'test.pdf')
    sys.exit(1)
    pdfs = generate_barcodes(data, w)
    with open('test.svg', 'wb') as f:
        f.write(pdfs)
    # with open('test.svg', 'rb') as f:
    #     pdfs = f.read()

    img = cairosvg.svg2png(bytestring=pdfs, output_height=76)
    im = Image.open(BytesIO(img))
    # imgs = pdf2image.convert_from_bytes(pdfs, 600)
    # imgs = pdf2image.convert_from_bytes(pdfs, size=(None, 76))
    # im = imgs[0]

    # set_h = 76
    # im = im.convert('1')
    # im = im.convert('1', dither=PIL.Image.Dither.NONE)
    # im = im.convert('1', dither=Image.Dither.NONE)
    # im = im.resize((int(im.width / im.height * set_h), set_h), resample=Image.Resampling.LANCZOS)
    # im = im.convert('1', dither=PIL.Image.Dither.NONE)

    for col in range(im.width):
        print('col: ', col, 'data', ','.join([str(im.getpixel((col, im.height - i - 1))) for i in range(im.height)]))

    im.save('test1.png')

    im.close()