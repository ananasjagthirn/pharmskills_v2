from utils import run_page

INDS = {"blähungen", "durchfall", "verstopfung", "sodbrennen",
        "übelkeit/erbrechen", "reizdarmsyndrom", "magen-darm-beschwerden", "hämorrhoiden"}
run_page("Magen-Darm-Erkrankungen", INDS, "mgd")
