"""Parse the statements in the inbox folder into lines files and check them. Writes nothing to Dataverse.

    python scripts/statement_parse.py "<inbox folder>" <out folder>

Handles ANZ Plus PDFs (statements and "Transaction List" exports), ANZ New Zealand PDFs ("<account number>_Statement_<date>.pdf",
NZD), Kogan Money PDFs and AMEX .xlsx (statements, or the current cycle's export named "AMEX <export date>.xlsx")
(Wise: scripts/wise_lines.py). For each file it writes
<out>/<file name>.json (the lines, in the format statement_compare.py reads) and <out>/_statements.json
(account, period, balances), and prints the checks: ANZ running balance line by line, Kogan and AMEX summary
totals, filename against the period, gaps or overlaps between consecutive statements, and opening balance
against the previous closing balance. Keep the out folder outside the repo.

Needs pypdf and openpyxl. PDFs are read with pypdf in layout mode, because pdfplumber does not install on
ARM64 Windows; ANZ signs come from the running balance change.
"""
import re, json, os, sys, glob, datetime as dt

import pypdf
from itertools import groupby

INBOX, OUT = os.path.join(sys.argv[1], ""), sys.argv[2]
os.makedirs(OUT, exist_ok=True)
MON = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}
issues = []


def money(s):
    return float(s.replace("$", "").replace(",", ""))


def issue(f, msg):
    issues.append(f"{f}: {msg}")


SKIP = ("Effective Date", "Account Statement", "Date ", "Opening Balance", "Australia and", "AFSL", "Please",
        "ANZ Plus", "If you", "For information", "a complaint", "www.")


def pdf_text(path):
    r = pypdf.PdfReader(path)
    return "\n".join(f"=== PAGE {i + 1}\n" + pg.extract_text(extraction_mode="layout") for i, pg in enumerate(r.pages))


def anz(path):
    f = os.path.basename(path)
    t = pdf_text(path)
    m = re.search(r"(\d+) (\w+) (\d{4}) - (\d+) (\w+) (\d{4})", t)
    if m:
        ps = dt.date(int(m[3]), MON[m[2][:3]], int(m[1]))
        pe = fdate = dt.date(int(m[6]), MON[m[5][:3]], int(m[4]))
    else:  # "Transaction List": from "Commencing <date>" to the day before it was generated
        cm = re.search(r"Commencing (\d+) (\w+) (\d{4})", t)
        gm = re.search(r"generated on (\d+) (\w+) (\d{4})", t)
        ps = dt.date(int(cm[3]), MON[cm[2][:3]], int(cm[1]))
        fdate = dt.date(int(gm[3]), MON[gm[2][:3]], int(gm[1]))
        pe = fdate - dt.timedelta(days=1)
    hm = re.search(r"\d{3} \d{3}\s+(\d{3} \d{3} \d{3})\s+(\$[\d,.]+)\s+(\$[\d,.]+)", t)
    acct, opening, closing = hm[1].replace(" ", ""), money(hm[2]), money(hm[3])
    fm = re.search(r"(\d{4})-(\d\d)-(\d\d) - .* x(\d{4})", f)
    if dt.date(int(fm[1]), int(fm[2]), int(fm[3])) not in (fdate, pe):
        issue(f, f"filename date != period end {pe}")
    if not acct.endswith(fm[4]):
        issue(f, f"filename x{fm[4]} != account {acct}")
    om = re.search(r"^\s+Opening Balance\s+(\$[\d,.]+)\s*$", t, re.M)
    if om and abs(money(om[1]) - opening) > .005:
        issue(f, f"footer opening {om[1]} != header {opening}")
    lines, cur = [], None
    for ln in t.splitlines():
        mm = re.match(r"^(\d\d) (\w{3})\s{2,}(.+?)\s{2,}(\$[\d,.]+)\s+(\$[\d,.]+)\s*$", ln)
        if mm:
            mo = MON[mm[2]]
            d = dt.date(pe.year if mo <= pe.month else pe.year - 1, mo, int(mm[1]))
            cur = {"date": d.isoformat(), "description": mm[3].strip(), "amt": money(mm[4]), "balance": money(mm[5])}
            lines.append(cur)
            continue
        s = ln.strip()
        if not s:
            continue
        if s.startswith("Effective Date") and cur:
            cur["effective"] = s[15:]
        elif cur and ln.startswith(" ") and not s.startswith(SKIP) and (len(ln) - len(ln.lstrip())) < 30 \
                and not re.search(r"\d+ \w+ \d{4} - ", s):
            cur["description"] += " " + s
        else:
            cur = None
    lines.reverse()  # oldest first
    prev = opening
    for i, l in enumerate(lines, 1):
        d = l["description"]
        d = re.sub(r"\$(\d+) (\d+) -", r"$\1\2 -", d)          # "$26 2 -" wrapped mid-number
        d = re.sub(r"#(\d+) (\d+)$", r"#\1\2", d)                # "#5 65862"
        l["description"] = d
        rm = re.search(r"#(\d+)$", d)
        if rm:
            l["bank_reference"] = rm[1]
        l["line_number"] = i
        l["posted_date"] = l["date"]
        if l.get("effective"):
            e = dt.datetime.strptime(l.pop("effective").strip(), "%d/%m/%Y").date()
            l["date"] = e.isoformat()
        diff = round(l["balance"] - prev, 2)
        if abs(abs(diff) - l["amt"]) > 0.005:
            issue(f, f"balance chain break at {l['date']} {l['description'][:40]} amt {l['amt']} bal {l['balance']} prev {prev}")
            l["amount"] = -l["amt"]
        else:
            l["amount"] = diff
        prev = l["balance"]
        l.pop("amt")
        if not (ps.isoformat() <= l["posted_date"] <= pe.isoformat()):
            issue(f, f"posted date {l['posted_date']} outside period")
    if lines and abs(lines[-1]["balance"] - closing) > 0.005:
        issue(f, f"last balance {lines[-1]['balance']} != closing {closing}")
    if not lines and abs(opening - closing) > .005:
        issue(f, "no lines but opening != closing")
    return dict(file=f, account="x" + fm[4], kind="PDF", start=ps.isoformat(), end=pe.isoformat(),
                opening=opening, closing=closing, lines=lines, interim=not m)


def anz_nz(path):
    """ANZ Bank New Zealand statement. Amounts are NZD; Original Amount / Currency repeat them in NZD."""
    f = os.path.basename(path)
    t = pdf_text(path)
    if not re.search(r"Statement ?period", t):  # pypdf layout mode returns nothing for these PDFs
        import pdfplumber
        with pdfplumber.open(path) as pdf:
            t = "\n".join(pg.extract_text(layout=True) or "" for pg in pdf.pages)
    m = re.search(r"Statement ?period\s*(\d+) (\w{3}) (\d{4}) - (\d+) (\w{3}) (\d{4})", t)
    ps = dt.date(int(m[3]), MON[m[2]], int(m[1]))
    pe = dt.date(int(m[6]), MON[m[5]], int(m[4]))
    acct = re.search(r"Account ?number\s*(\d\d-\d{4}-\d{7}-\d\d)", t)[1]
    if not f.startswith(acct) and not f.startswith("ANZ NZ Go "):
        issue(f, f"filename != account {acct}")
    opening = money(re.search(r"Opening ?balance\s+([\d,]+\.\d\d)", t)[1])
    tm = re.search(r"Totals ?at ?end ?of ?period\s+\$([\d,.]+)\s+\$([\d,.]+)\s+\$([\d,.]+)", t)
    out_total, in_total, closing = money(tm[1]), money(tm[2]), money(tm[3])
    lines, cur = [], None
    for ln in t.splitlines():
        mm = re.match(r"^\s*(\d\d) (\w{3})\s+(.+?)\s+([\d,]+\.\d\d)\s+([\d,]+\.\d\d)\s*$", ln)
        if mm and mm[2] in MON:
            mo = MON[mm[2]]
            d = dt.date(pe.year if mo <= pe.month else pe.year - 1, mo, int(mm[1]))
            cur = {"date": d.isoformat(), "description": re.sub(r"\s+", " ", mm[3].strip()),
                   "amt": money(mm[4]), "balance": money(mm[5])}
            lines.append(cur)
            continue
        om = re.search(r"Orig date (\d\d/\d\d/\d{4})", ln)
        if om and cur:
            cur["orig"] = om[1]
        cur = None if not om else cur
    prev = opening
    for i, l in enumerate(lines, 1):
        l["line_number"] = i
        l["posted_date"] = l["date"]
        if l.get("orig"):
            l["date"] = dt.datetime.strptime(l.pop("orig"), "%d/%m/%Y").date().isoformat()
        l["description"] = re.sub(r" ?\d{6}\*+ ?\d{4} C$", "", l["description"])  # card number on EFTPOS lines
        diff = round(l["balance"] - prev, 2)
        if abs(abs(diff) - l["amt"]) > 0.005:
            issue(f, f"balance chain break at {l['date']} {l['description'][:40]}")
            diff = -l["amt"]
        l["amount"] = diff
        l["original_amount"], l["original_currency"] = diff, "NZD"
        prev = l["balance"]
        l.pop("amt")
    if round(sum(-l["amount"] for l in lines if l["amount"] < 0), 2) != out_total or \
            round(sum(l["amount"] for l in lines if l["amount"] > 0), 2) != in_total:
        issue(f, "withdrawal or deposit total differs from the statement")
    if lines and abs(lines[-1]["balance"] - closing) > 0.005:
        issue(f, f"last balance {lines[-1]['balance']} != closing {closing}")
    return dict(file=f, account="NZGo", kind="PDF", start=ps.isoformat(), end=pe.isoformat(),
                opening=opening, closing=closing, lines=lines)


def kogan(path):
    f = os.path.basename(path)
    t = pdf_text(path)
    m = re.search(r"Statement Period\s+(\d+) (\w{3}) (\d\d) to (\d+) (\w{3}) (\d\d)", t)
    ps = dt.date(2000 + int(m[3]), MON[m[2]], int(m[1]))
    pe = dt.date(2000 + int(m[6]), MON[m[5]], int(m[4]))
    fm = re.search(r"_(\d{8})", f)
    if fm[1] != pe.strftime("%Y%m%d"):
        issue(f, f"filename date != period end {pe}")

    def bal(label):
        mm = re.search(label + r"\s+\$([\d,.]+)( Cr| Dr)?", t)
        v = money(mm[1])
        return v if mm[2] == " Cr" else -v
    opening, closing = bal("Opening Balance"), bal("= Closing Balance")
    cr = money(re.search(r"Payments & credits received\s+\$([\d,.]+)", t)[1])
    dr = money(re.search(r"Purchases & other debits\s+\$([\d,.]+)", t)[1])
    intr = money(re.search(r"Interest & other charges\s+\$([\d,.]+)", t)[1])
    lines = []
    for mm in re.finditer(r"^\s+(\d\d)/(\d\d)/(\d\d)\s+(\d\d)/(\d\d)/(\d\d)\s+(.+?)\s{2,}\$([\d,.]+) (Cr|Dr)\s*$", t, re.M):
        d = dt.date(2000 + int(mm[6]), int(mm[5]), int(mm[4]))
        pd = dt.date(2000 + int(mm[3]), int(mm[2]), int(mm[1]))
        a = money(mm[8])
        a = a if mm[9] == "Cr" else -a
        lines.append({"date": d.isoformat(), "posted_date": pd.isoformat(), "description": mm[7].strip(), "amount": a,
                      "line_number": len(lines) + 1})
        if not (ps <= pd <= pe):
            issue(f, f"processed date {pd} outside period: {mm[7].strip()}")
    scr = round(sum(l["amount"] for l in lines if l["amount"] > 0), 2)
    sdr = round(-sum(l["amount"] for l in lines if l["amount"] < 0), 2)
    if abs(scr - cr) > .005:
        issue(f, f"credits sum {scr} != summary {cr}")
    if abs(sdr - dr - intr) > .005:
        issue(f, f"debits sum {sdr} != summary {dr}+{intr}")
    if abs(opening + scr - sdr - closing) > .005:
        issue(f, f"opening {opening} + lines != closing {closing}")
    return dict(file=f, account="Kogan", kind="PDF", start=ps.isoformat(), end=pe.isoformat(),
                opening=opening, closing=closing, lines=lines)


def amex(path):
    import openpyxl
    f = os.path.basename(path)
    ws = openpyxl.load_workbook(INBOX + f, data_only=True).worksheets[0]
    rows = list(ws.iter_rows(values_only=True))
    m = re.search(r"/ (\w{3}) (\d+), (\d{4}) to (\w{3}) (\d+), (\d{4})", rows[0][1])
    ps = dt.date(int(m[3]), MON[m[1]], int(m[2]))
    pe = dt.date(int(m[6]), MON[m[4]], int(m[5]))
    sm = {r[0]: r[1] for r in list(wb_rows(INBOX + f, "Transaction Summary")) if r and r[0] and r[1] is not None}
    interim = "Statement Balance" not in sm
    if interim:  # export of the current cycle: ends on the (last) date in the file name
        pe = dt.date.fromisoformat(re.findall(r"\d{4}-\d\d-\d\d", f)[-1])
    elif f[5:15] != pe.isoformat():
        issue(f, f"filename date != period end {pe}")
    hi = next(i for i, r in enumerate(rows) if r[0] == "Date")
    H = rows[hi]
    lines = []
    for r in rows[hi + 1:]:
        if r[0] is None:
            continue
        rec = dict(zip(H, r))
        d = dt.datetime.strptime(rec["Date"], "%d/%m/%Y").date()
        pdte = dt.datetime.strptime(rec["Date Processed"], "%d/%m/%Y").date()
        l = {"date": d.isoformat(), "posted_date": pdte.isoformat(),
             "description": re.sub(r"\s+", " ", rec["Description"]).strip(),
             "amount": -round(float(rec["Amount"]), 2), "bank_reference": rec.get("Reference"),
             "card_holder": rec.get("Card Member"), "line_number": len(lines) + 1}
        fs = rec.get("Foreign Spend Amount")
        if fs is not None and str(fs).strip():
            issue(f, f"foreign spend amount not handled: {l['description']} {fs}")
        if rec.get("Additional Information") and str(rec["Additional Information"]).strip():
            cat = str(rec["Additional Information"]).split("\n")[0].strip()
            if cat:
                l["bank_category"] = cat.title()
        lines.append(l)
        if not (ps <= pdte <= pe) and not (ps <= d <= pe):
            issue(f, f"date {d}/{pdte} outside period: {l['description']}")
    refs = [l["bank_reference"] for l in lines if l["bank_reference"]]
    if len(refs) != len(set(refs)):
        issue(f, "duplicate Reference values inside the file")
    opening = -round(float(sm["Previous Balance"]), 2)
    closing = -round(float(sm.get("Statement Balance", sm.get("Total Balance"))), 2)
    pay, chg = float(sm["Payments & Credits"]), float(sm["Charges & Adjustments"])
    scr = round(sum(l["amount"] for l in lines if l["amount"] > 0), 2)
    sdr = round(-sum(l["amount"] for l in lines if l["amount"] < 0), 2)
    if abs(scr + pay) > .005:
        issue(f, f"credits {scr} != summary {pay}")
    if abs(sdr - chg) > .005:
        issue(f, f"charges {sdr} != summary {chg}")
    if abs(opening + scr - sdr - closing) > .005:
        issue(f, f"previous {opening} + lines != statement balance {closing}")
    lines.reverse()  # oldest first
    for i, l in enumerate(lines, 1):
        l["line_number"] = i
    return dict(file=f, account="AMEX", kind="CSV", start=ps.isoformat(), end=pe.isoformat(),
                opening=opening, closing=closing, lines=lines, interim=interim)


def wb_rows(path, sheet):
    import openpyxl
    return openpyxl.load_workbook(path, data_only=True)[sheet].iter_rows(values_only=True)


stmts = []
for p in sorted(glob.glob(INBOX + "*")):
    b = os.path.basename(p)
    if re.match(r"\d\d-\d{4}-\d{7}-\d\d_Statement_.*\.pdf$", b) or (b.startswith("ANZ NZ Go ") and b.endswith(".pdf")):
        stmts.append(anz_nz(p))
    elif b.startswith("ANZ") and b.endswith(".pdf"):
        stmts.append(anz(p))
    elif b.startswith("Kogan") and b.endswith(".pdf"):
        stmts.append(kogan(p))
    elif b.startswith("AMEX") and b.endswith(".xlsx"):
        stmts.append(amex(p))
for acc, grp in groupby(sorted(stmts, key=lambda s: (s["account"], s["start"])), key=lambda s: s["account"]):
    g = list(grp)
    for a, b in zip(g, g[1:]):
        if (dt.date.fromisoformat(b["start"]) - dt.date.fromisoformat(a["end"])).days != 1:
            issue(b["file"], f"gap/overlap: previous ends {a['end']}, this starts {b['start']}")
        if a["closing"] is not None and abs(a["closing"] - b["opening"]) > .005:
            issue(b["file"], f"opening {b['opening']} != previous closing {a['closing']}")
for s in stmts:
    net = round(sum(l["amount"] for l in s["lines"]), 2)
    print(f"{s['account']:6} {s['start']}..{s['end']} {s['kind']} lines={len(s['lines']):3} "
          f"open={s['opening']} close={s['closing']} net={net}  {s['file']}")
    json.dump(s["lines"], open(os.path.join(OUT, s["file"] + ".json"), "w"), indent=1)
json.dump([{k: v for k, v in s.items() if k != "lines"} | {"count": len(s["lines"])} for s in stmts],
          open(os.path.join(OUT, "_statements.json"), "w"), indent=1)
print("ISSUES:")
print("\n".join(issues) or "none")
