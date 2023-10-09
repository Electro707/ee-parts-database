import logging
import typing
import os
try:
    from blabel import label_tools
    from blabel import LabelWriter
    from PIL import Image
    import barcode as python_barcode
    from weasyprint import CSS
except ImportError:
    available = False
else:
    available = True


def _make_barcode(data: str, **writter_options) -> Image.Image:
    """Makes a barcode image"""
    constructor = python_barcode.get_barcode_class('code128')
    data = str(data).zfill(constructor.digits)
    barcode_img = constructor(data, writer=python_barcode.writer.ImageWriter())
    return barcode_img.render(writer_options=writter_options)


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

    html_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "label_template.html")

    with open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "label_template.css"), 'r') as f:
        css = f.read()

    css += f"@page {{ height: {label_width}mm;  padding: 0.5mm; }}"
    css += f"img {{ height:{label_width - 2}mm;  }}"

    records = [{'ipn': i} for i in ipns]
    for i, r in enumerate(records):
        img = _make_barcode(r['ipn'], module_height=label_width*0.7, module_width=1.0, text_distance=7.5, font_size=18, dpi=600)

        r['page_height'] = f'{label_width}mm'
        r['page_width'] = f"{(img.size[0] * (label_width - 2) / img.size[1]) + 5}mm"
        r['barcode_data'] = label_tools.pil_to_html_imgdata(img)
        r['page_id'] = f'page{i}'

        css += f"@page page{i} {{ width: {r['page_width']}; }}"

    css = CSS(string=css)

    label_writer = LabelWriter(item_template_path=html_path, default_stylesheets=(css, ))
    label_writer.write_labels(records, target=export_path)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    w = 28.0
    data = [f'TESTawdadawdawda{i:05d}' for i in range(5)]
    data.append("SMALL")
    export_barcodes(data, w, 'test.pdf')
