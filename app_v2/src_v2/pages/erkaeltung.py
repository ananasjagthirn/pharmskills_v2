from utils import run_page

INDS = {"husten", "schnupfen", "halsschmerzen/heiserkeit", "fieber/schmerzen"}
run_page("Erkältungssymptomen", INDS, "erk")
