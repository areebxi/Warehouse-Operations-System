"""
GUI utility wrapper functions.
"""

from src.io.file_handlers import find_design_file, find_design_file_vba_logic


def find_design_file_wrapper(gui, sku):
    """Find design file for given SKU"""
    return find_design_file(sku, gui.designs_folder)


def find_design_file_vba_logic_wrapper(
    gui,
    order_number,
    duplicate_index=0,
    folder_type=None,
    exclude_path=None,
):
    """Find design file following VBA logic: Single first, then Double"""
    return find_design_file_vba_logic(
        order_number,
        duplicate_index,
        single_designs_folder=gui.single_designs_folder,
        double_designs_folder=gui.double_designs_folder,
        folder_type=folder_type,
        exclude_path=exclude_path,
    )

