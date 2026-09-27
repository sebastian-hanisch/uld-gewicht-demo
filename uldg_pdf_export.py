"""Erzeugt einen downloadbaren Packplan als PDF (in-memory, kein Zwischenspeichern auf Disk): Einstellungen,
Kennzahlen beider Regeln, die Meldung der gezeigten Instanz und die Positionsliste beider Packungen.

fpdf2-Fallstricke (siehe DEMO-PLAYBOOK Abschnitt 7): echte Umlaute sind in den Kernschriften unproblematisch,
Gedankenstrich (-) und Euro-Zeichen (EUR statt Symbol) vermeiden - hier kommt ohnehin kein Geldbetrag vor."""
import time

import uldg_constants as C
from uldg_format import fmt_num, fmt_pct


def generate_uldg_pdf(settings: dict, live: dict, cell: dict) -> bytes:
    from fpdf import FPDF
    from fpdf.enums import XPos, YPos

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 10, "Packplan - ULD-Beladung", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 6, f"Erstellt: {time.strftime('%d.%m.%Y %H:%M')} Uhr", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Einstellungen", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Container: {C.W:.0f} x {C.D:.0f} x {C.H:.0f} cm, Kontur {C.CONTOUR_LABEL[settings['contour']]}",
              new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.cell(0, 6, f"Boxen: {settings['n_boxes']}, Dichtestreuung {fmt_num(settings['cv'], 1)}, "
                   f"Toleranz {fmt_pct(settings['tol'], 0)}, Seed {settings['seed']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Kennzahlen beider Regeln (diese Instanz)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(235, 235, 235)
    headers = ["Kennzahl", "H_vol", "H_cg"]
    widths = [70, 55, 55]
    for h, w in zip(headers, widths):
        pdf.cell(w, 7, h, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
    pdf.ln(7)
    pdf.set_font("Helvetica", "", 9)
    ox_v, oy_v = live["offset_vol"]
    ox_c, oy_c = live["offset_cg"]
    rows = [
        ("Auslastung", fmt_pct(live["util_vol"]), fmt_pct(live["util_cg"])),
        ("Unplatzierte Boxen", str(len(live["unplaced_vol"])), str(len(live["unplaced_cg"]))),
        ("Schwerpunkt-Offset x (cm)", f"{ox_v:.1f}", f"{ox_c:.1f}"),
        ("Schwerpunkt-Offset y (cm)", f"{oy_v:.1f}", f"{oy_c:.1f}"),
        ("Toleranz verletzt", "ja" if live["violation_vol"] else "nein", "ja" if live["violation_cg"] else "nein"),
    ]
    for row in rows:
        for val, w in zip(row, widths):
            pdf.cell(w, 6, val, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(6)
    pdf.ln(4)

    pdf.set_font("Helvetica", "B", 11)
    pdf.cell(0, 8, "Messreihe (200 Instanzen dieser Zelle)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.multi_cell(0, 5, f"H_vol verletzt in {fmt_pct(cell['violation_rate_vol'])} der Instanzen, "
                         f"H_cg in {fmt_pct(cell['violation_rate_cg'])}.")
    pdf.ln(3)

    for rule_label, placed in (("H_vol (Volumen)", live["placed_vol"]), ("H_cg (schwerpunkt-bewusst)", live["placed_cg"])):
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(0, 8, f"Positionsliste {rule_label}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(235, 235, 235)
        headers2 = ["#", "Position (x,y,z)", "Masse (BxTxH)", "Gewicht (kg)"]
        widths2 = [10, 55, 55, 30]
        for h, w in zip(headers2, widths2):
            pdf.cell(w, 7, h, border=1, fill=True, new_x=XPos.RIGHT, new_y=YPos.TOP)
        pdf.ln(7)
        pdf.set_font("Helvetica", "", 9)
        sorted_placed = sorted(placed, key=lambda p: (p.z, p.y, p.x))
        for i, p in enumerate(sorted_placed):
            row2 = [str(i + 1), f"({p.x:.0f}, {p.y:.0f}, {p.z:.0f}) cm",
                    f"{p.box.w:.0f} x {p.box.d:.0f} x {p.box.h:.0f} cm", f"{p.box.weight:.1f}"]
            for val, w in zip(row2, widths2):
                pdf.cell(w, 6, val, border=1, new_x=XPos.RIGHT, new_y=YPos.TOP)
            pdf.ln(6)
        pdf.ln(4)

    return bytes(pdf.output())
