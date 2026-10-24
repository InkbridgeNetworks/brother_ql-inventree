"""Pin placement of P-touch labels on the print head of each model.

The expected pins for the PT-P900 series come from Brother's 'Raster Command
Reference PT-P900/P900W/P950NW' version 1.02, section 2 'Print Data', page 20.
The expected pins for the 180 dpi models are the geometry in
brother_ql.labels, which the 360 dpi geometry must not change.

Run with: python -m unittest discover tests
"""

import logging
import unittest

from PIL import Image

from brother_ql.conversion import convert
from brother_ql.raster import BrotherQLRaster

logging.disable(logging.WARNING)


def inked_pins(model, label):
    """Return (first pin, last pin) that convert() inks for a full-width label"""
    qlr = BrotherQLRaster(model)
    captured = {}
    add_raster_data = qlr.add_raster_data

    def capture(image, second_image=None):
        captured["image"] = image.copy()
        return add_raster_data(image, second_image)

    qlr.add_raster_data = capture
    convert(qlr, [Image.new("1", (300, 40), 0)], label, rotate="0", cut=False)
    # Non-zero pixels in the raster image are the dots that the printer prints
    box = captured["image"].convert("L").getbbox()
    return box[0], box[2] - 1


#: Brother's TZe tape table: label -> (left margin pins, print area pins)
PT_P900_SERIES = {
    "pt12": (197, 150),
    "pt18": (155, 234),
    "pt24": (112, 320),
    "pt36": (45, 454),
}

#: Geometry of the 128-pin, 180 dpi print head: label -> (first pin, last pin)
PT_180DPI = {
    "pt12": (29, 98),
    "pt18": (8, 119),
    "pt24": (0, 127),
}


class TestPTouchGeometry(unittest.TestCase):

    def test_pt_p900_series_matches_brother_table(self):
        for model in ("PT-P900W", "PT-P950NW"):
            for label, (left_margin, print_area) in PT_P900_SERIES.items():
                with self.subTest(model=model, label=label):
                    self.assertEqual(inked_pins(model, label),
                                     (left_margin, left_margin + print_area - 1))

    def test_180dpi_models_unchanged(self):
        for model in ("PT-E550W", "PT-P700", "PT-P750W"):
            for label, pins in PT_180DPI.items():
                with self.subTest(model=model, label=label):
                    self.assertEqual(inked_pins(model, label), pins)


if __name__ == "__main__":
    unittest.main()
