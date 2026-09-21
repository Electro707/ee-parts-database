def test_display_order():
    from e7epd import E7EPD
    all_comp_type = E7EPD.comp_types
    for c in all_comp_type:
        for t in c.table_display_order:
            assert t in c.items