from utils import run_page, load_data

df = load_data()
INDS = set(i for inds in df["ind_list"] for i in inds)
run_page("Erkältungssymptomen und Magen-Darm-Erkrankungen", INDS, "alle")
