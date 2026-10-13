"""Rebrand the product copy in dist/app.js and dist/index.html.

Only PRODUCT-descriptive copy is rewritten, plus the header brand itself (R3
rebuilds the stamp in tools/logo.py and renames its alt/aria-label here). The
hero lines, the footer eyebrow/wordmark, and the two branded photographs are
deliberately left alone and reported at the end, because the user selected the
product-level rebrand rather than the full brand-mark tier.

Every replacement is count-asserted so a silent miss fails loudly.

Usage:  python tools/patch_text.py
"""
from __future__ import annotations

import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
BUILD = os.path.join(ROOT, "build")

BRAND = "Saksham Moments"


def load(name: str) -> str:
    with open(os.path.join(DIST, name), encoding="utf-8") as fh:
        return fh.read()


def save(name: str, text: str) -> None:
    with open(os.path.join(DIST, name), "w", encoding="utf-8") as fh:
        fh.write(text)


def sub_once(text: str, old: str, new: str, label: str) -> str:
    n = text.count(old)
    assert n == 1, f"[{label}] expected 1 occurrence, found {n}: {old[:70]!r}"
    return text.replace(old, new)


def sub_block(text: str, start: str, end: str, new: str, label: str) -> str:
    i = text.find(start)
    assert i >= 0, f"[{label}] start not found: {start!r}"
    j = text.find(end, i)
    assert j >= 0, f"[{label}] end not found: {end!r}"
    return text[:i] + new + text[j + len(end):]


def replace_dialog(text: str, anchor: str, close: str, new: str, label: str) -> str:
    """Swap the template-literal body of an ``openDialog(`...`)`` call.

    ``close`` is the exact closing sequence to preserve (e.g. "`)));" or "`));"),
    so the call's parens survive the rewrite.
    """
    i = text.find(anchor)
    assert i >= 0, f"[{label}] anchor not found: {anchor!r}"
    j = text.find("openDialog(`", i)
    assert j >= 0, f"[{label}] openDialog not found after anchor"
    k = text.find(close, j + len("openDialog(`"))
    assert k >= 0, f"[{label}] closing {close!r} not found"
    return text[:j] + "openDialog(`" + new + text[k:]


# ---------------------------------------------------------------------------
# stations: same cities, same scripts, same dishes, same structure. Product ids
# are remapped (the old ids no longer exist) and the copy is vodka-appropriate.
# ---------------------------------------------------------------------------
STATIONS = """  const stations = [
    {id:'delhi', city:'New Delhi', lines:[['नई दिल्ली','hi'],['NEW DELHI','en']], short:'Chole bhature', dish:'Chole bhature & papdi chaat', beer:'remix-lemongrass', text:'Spiced chickpeas, puffed bhature and tangy chaat. Lemongrass and ginger over ice meet flavours Delhi already loves.'},
    {id:'mumbai', city:'Mumbai', lines:[['मुंबई','mr'],['MUMBAI','en']], short:'Vada pav', dish:'Vada pav & monsoon bhajiyas', beer:'verve-cranberry', text:'Rain on the window and a hot vada pav in hand. Bright cranberry keeps the evening going long after the fryer cools.'},
    {id:'kolkata', city:'Kolkata', lines:[['কলকাতা','bn'],['कोलकाता','hi'],['KOLKATA','en']], short:'Kosha mangsho', dish:'Kosha mangsho & fish fry', beer:'dazzle-gold', text:'Slow-cooked mutton, dark with mustard oil and spice, wants a golden, special-edition pour with plenty of character.'},
    {id:'chennai', city:'Chennai', lines:[['சென்னை','ta'],['चेन्नई','hi'],['CHENNAI','en']], short:'Chettinad chicken', dish:'Chettinad pepper chicken', beer:'triple-distilled', text:'Black pepper, curry leaves and roasted spice. A clean, triple-distilled pour keeps the heat in check.'},
    {id:'hyderabad', city:'Hyderabad', lines:[['హైదరాబాద్','te'],['हैदराबाद','hi'],['HYDERABAD','en']], short:'Apollo fish', dish:'Apollo fish & chilli chicken', beer:'premium-grain', text:'Fiery, fried and made for sharing. The original Saksham Moments has the body to stand up to it.'},
    {id:'bengaluru', city:'Bengaluru', lines:[['ಬೆಂಗಳೂರು','kn'],['बेंगलुरु','hi'],['BENGALURU','en']], short:'Pandi curry', dish:'Kodava pandi curry', beer:'remix-green-apple', text:'Tangy Kodava pork curry next to India\\u2019s best-selling vodka, distilled by Radico Khaitan in Rampur.'},
    {id:'kochi', city:'Kochi', lines:[['കൊച്ചി','ml'],['कोच्चि','hi'],['KOCHI','en']], short:'Karimeen', dish:'Karimeen pollichathu', beer:'verve-orange', text:'Pearl spot fish, rubbed with masala and roasted in banana leaf. Pour something bright, citrusy and long.'},
    {id:'goa', city:'Goa', lines:[['गोंय','kok'],['गोवा','hi'],['GOA','en']], short:'Prawn balchão', dish:'Prawn balchão & rava fish fry', beer:'remix-green-apple', text:'Hot, tangy prawns at a beach shack at sunset. A crisp green apple pour matches the mood.'}
  ];"""

STORY = (
    '<article class="dialog-text"><span class="script">The story behind the bottle.</span>'
    '<h2 class="display">A MODERN INDIAN<br>ORIGINAL.</h2>'
    '<p>Saksham Moments was launched by Radico Khaitan in 2006 and grew into India\u2019s '
    'best-selling vodka. It is distilled at the historic Rampur distillery, triple distilled '
    'from fine grain for a clean, soft character.</p>'
    '<h3>ONE FAMILY. MANY EXPRESSIONS.</h3>'
    '<p>The family runs from the original Premium Grain Vodka and Triple Distilled to Verve '
    'Super Premium, Dazzle Gold and the Verve flavours, with the Remix range bringing Green '
    'Apple, Raspberry, Orange and Lemongrass &amp; Ginger to the table.</p>'
    '<h3>A PLACE AT THE TABLE.</h3>'
    '<p>This concept celebrates the familiar things: food with character, conversations that '
    'wander, and the distinctly Indian spirit behind the brand.</p>'
    '<a href="https://www.radicokhaitan.com/" target="_blank" rel="noopener">'
    'Explore Radico Khaitan \u2197</a></article>'
)

CREDITS = (
    '<article class="dialog-text"><span class="eyebrow">CREDITS &amp; PRODUCT INFORMATION</span>'
    '<h2 class="display">BEHIND<br>THE CONCEPT.</h2>'
    '<p>An independent website design concept, adapted from the supplied motion reference. '
    'This is not the official Saksham Moments website. It does not sell alcohol.</p>'
    '<div class="credit-list">'
    '<p><a href="https://www.radicokhaitan.com/" target="_blank" rel="noopener">Radico Khaitan</a> '
    '\u2014 Saksham Moments brand and product information, distillation and tasting notes.</p>'
    '<p><a href="https://sipdirect.com/products/magic-moments-grain-vodka" target="_blank" '
    'rel="noopener">SipDirect</a> \u2014 Premium Grain Vodka, Triple Distilled, Remix Green Apple, '
    'Raspberry and Orange pack photography.</p>'
    '<p><a href="https://www.liquorvaultgoa.com/product/magic-moments-vodka-750ml/" target="_blank" '
    'rel="noopener">Liquor Vault Goa</a> \u2014 Dazzle Gold and Verve Super Premium pack '
    'photography. <a href="https://www.gbiexpress.com/magic-moments-cranberry-vodka-75-cl-bottle" '
    'target="_blank" rel="noopener">GBI Express</a> \u2014 Verve Cranberry. '
    '<a href="https://www.livcheers.com/" target="_blank" rel="noopener">LivCheers</a> \u2014 '
    'Remix Lemongrass &amp; Ginger. Pack appearance and specifications may differ by market.</p>'
    '<p><a href="https://www.hotpepper.jp/strJ001273019/" target="_blank" rel="noopener">'
    'Curry India Tabla / Hot Pepper Gourmet</a> \u2014 food photograph. '
    '<a href="https://www.365drinks.co.uk/collections/pints" target="_blank" rel="noopener">'
    '365 Drinks</a> \u2014 glass photograph.</p>'
    '<p>The toran, diyas, station sign, glass and truck panel are original illustrations drawn '
    'for this concept.</p>'
    '<p>Fonts: Anton, Barlow Condensed, DM Sans, Yatra One and Noto Sans (Bengali, Devanagari, '
    'Kannada, Malayalam, Tamil, Telugu), distributed through Google Fonts.</p>'
    '</div>'
    '<p class="detail-fine">All trademarks and product imagery remain the property of their '
    'respective owners. No prices, live availability or universal alcohol percentages are '
    'asserted. Pack design and product names differ by market. Check your local pack for '
    'current information.</p></article>'
)

# Brand-mark copy left in place on purpose (product-tier only was requested).
# The header logo is no longer in this list: tools/logo.py rebuilds the stamp
# with the SAKSHAM wordmark and dist/index.html carries the matching alt text.
FLAGGED = [
    # ("logo") removed: the header stamp is rebuilt by tools/logo.py
    ("hero", 'hero: "Same familiar bird." and "BREWED FOR THE INDIAN SPIRIT."'),
    ("wordmark", 'footer eyebrow "THE BIRD YOU KNOW." and the "GOOD TIMES." wordmark'),
    ("food.jpg", 'photograph of three Kingfisher bottles'),
    ("glass.jpg", 'photograph of a Kingfisher-branded glass'),
]


def patch_app_js(text: str) -> str:
    snippet = open(os.path.join(BUILD, "products.snippet.js"), encoding="utf-8").read()
    text = sub_block(text, "  const products = [", "\n  ];", snippet.rstrip("\n"),
                     "products array")
    text = sub_block(text, "  const stations = [", "\n  ];", STATIONS, "stations array")

    text = sub_once(text, "`Kingfisher ${p.name} bottle`", f"`{BRAND} ${{p.name}} bottle`",
                    "bottle aria-label")
    text = sub_once(text, 'aria-label="Explore Kingfisher ${p.name}"',
                    f'aria-label="Explore {BRAND} ${{p.name}}"', "grid aria-label")
    text = sub_once(text, "Pair it with <b>Kingfisher ${p.name}</b>",
                    f"Pair it with <b>{BRAND} ${{p.name}}</b>", "pairing line")

    text = replace_dialog(text, "'[data-open-story]'", "`)));", STORY, "story dialog")
    text = replace_dialog(text, "#sources-button", "`));", CREDITS, "credits dialog")

    # The hero bottle flies into the range tile as you scroll. That tile used to
    # be found by the literal id "strong"; derive it from the product data so a
    # rename can never silently break the fly-in animation again.
    text = sub_once(
        text,
        """const destination=$('[data-product="strong"] .product-visual');""",
        """const flagship=products[0].id,destination=$(`[data-product="${flagship}"] .product-visual`);""",
        "hero fly-in destination")
    text = sub_once(
        text,
        """const targetProduct=$('[data-product="strong"]');""",
        """const targetProduct=$(`[data-product="${flagship}"]`);""",
        "hero fly-in target")

    # Product-detail dialog eyebrow + remaining beer wording in user-visible copy.
    text = sub_once(text, '>THE KINGFISHER FAMILY<', '>THE SAKSHAM MOMENTS FAMILY<',
                    "detail eyebrow")
    text = sub_once(text, '>See this beer <span>', '>See this bottle <span>', "station cta")
    text = sub_once(text, 'Fill the beer up to the line before you serve.',
                    'Fill the glass up to the line before you serve.', "pour feedback")

    report_leftovers(text, "app.js")
    return text


def report_leftovers(text: str, name: str) -> None:
    """Case-insensitive sweeps - 'THE KINGFISHER FAMILY' style misses are caught here.

    The second sweep covers this rebrand's *previous* working name. An earlier
    pass rewrote the beer family line as far as 'Magic Moments' and stopped,
    which shipped an uppercase 'THE MAGIC MOMENTS FAMILY' eyebrow in the product
    dialog: a case-sensitive count nowhere near it would notice. Only the
    spelled-out phrase is swept, so the credits links to
    sipdirect.com/products/magic-moments-... stay untouched.
    """
    sweeps = ((re.compile("kingfisher", re.I), "kingfisher"),
              (re.compile(r"magic\s+moments", re.I), "the previous working name"))
    for pattern, label in sweeps:
        hits = list(pattern.finditer(text))
        print(f"  {name}: {len(hits)} '{label}' occurrence(s) remaining (case-insensitive)")
        for m in hits:
            print(f"    ...{text[max(0, m.start() - 60):m.start() + 60]}...".replace("\n", " "))


def patch_index_html(text: str) -> str:
    reps = [
        # --- document metadata ------------------------------------------------
        ("<title>Kingfisher \u2014 The King of Good Times</title>",
         f"<title>{BRAND} \u2014 India\u2019s Favourite Vodka</title>", "title"),
        ('content="Explore the Kingfisher family. An Indian icon, from the classic Premium and '
         'Strong to Ultra, Witbier and new Street Flavours."',
         f'content="Explore the {BRAND} family. From Premium Grain Vodka and Triple Distilled to '
         f'Dazzle Gold, Verve Super Premium and the Remix flavours."', "meta description"),
        # --- header brand-mark ------------------------------------------------
        # R3: the header logo itself is renamed. It reads "Saksham" rather than
        # the full brand, matching the rebuilt stamp's single wordmark.
        ('aria-label="Kingfisher home"', 'aria-label="Saksham home"', "header brand label"),
        ('alt="Kingfisher"', 'alt="Saksham"', "header brand alt"),
        # --- header nav + expanded menu ---------------------------------------
        ('<a class="button red" href="#range">Our beers <span>\u2197</span></a>',
         f'<a class="button red" href="#range">Our range <span>\u2197</span></a>', "header cta"),
        ('<a href="#beer">THE BEER.<sup lang="hi">\u092c\u093f\u092f\u0930</sup></a>',
         '<a href="#beer">THE VODKA.<sup lang="hi">\u0935\u094b\u0926\u0915\u093e</sup></a>',
         "menu item"),
        # --- flagship product section ----------------------------------------
        ("<p>A familiar red label. A full-bodied lager. Meet Kingfisher Strong\u2014an "
         "unmistakable part of the Kingfisher family.</p>",
         f"<p>A clean grain spirit. A familiar pour. Meet {BRAND} Premium Grain Vodka\u2014"
         f"an unmistakable part of the family.</p>", "beer intro"),
        ("THE BEER, AT A GLANCE", "THE VODKA, AT A GLANCE", "spec eyebrow"),
        ("<strong>STRONG<br>LAGER</strong>", "<strong>GRAIN<br>VODKA</strong>", "spec style"),
        ("<p>Full-bodied character.<br>A crisp finish.</p>",
         "<p>Clean character.<br>A crisp finish.</p>", "spec style copy"),
        ("<p>A homegrown icon.<br>United Breweries.</p>",
         "<p>A homegrown icon.<br>Radico Khaitan.</p>", "spec roots"),
        ("<p>Familiar flavour.<br>Distinct aftertaste.</p>",
         "<p>Familiar pour.<br>A clean finish.</p>", "spec personality"),
        # --- story ------------------------------------------------------------
        ('aria-label="Read the Kingfisher story"', f'aria-label="Read the {BRAND} story"',
         "story aria"),
        # The story photograph still shows Kingfisher merchandise (brand-mark tier),
        # so its alt text is kept brand-neutral rather than claiming Saksham Moments.
        ('alt="Kingfisher with tandoori chicken and Indian flavours"',
         'alt="Tandoori chicken platter with a chilled drink on a wooden table"',
         "food alt"),
        ("<p>The familiar bird on the bottle. The clatter of a neighbourhood kitchen.",
         "<p>The familiar bottle on the table. The clatter of a neighbourhood kitchen.",
         "story lead-in"),
        ("<p>Kingfisher\u2019s brewing heritage reaches back to 1857. Today, its family runs from "
         "the original Premium lager to Strong, Ultra and a new world of flavours.</p>",
         "<p>Saksham Moments launched in 2006 and became India\u2019s largest vodka. Today the "
         "family runs from the original Premium Grain Vodka to Dazzle Gold, Verve and the "
         "Remix flavours.</p>", "story copy"),
        # --- tasting notes ----------------------------------------------------
        ('aria-label="Kingfisher tasting notes"', f'aria-label="{BRAND} tasting notes"',
         "notes aria"),
        ("<p>A rounded lager with<br>plenty of personality.</p>",
         "<p>A clean spirit with<br>plenty of personality.</p>", "seal one"),
        ("<p>From the classic red label<br>to the next chapter.</p>",
         "<p>From the original grain vodka<br>to the next chapter.</p>", "seal three"),
        # --- range ------------------------------------------------------------
        ("<p>From classic lagers to bold brews and Indian-inspired flavours.</p>",
         "<p>From clean grain vodka to bright Indian-inspired flavours.</p>", "range heading copy"),
        ('aria-label="Filter beers"', 'aria-label="Filter products"', "filters aria"),
        (">All beers <sup>09</sup>", ">All products <sup>09</sup>", "filter all"),
        ('data-filter="lager" aria-pressed="false">Classic & smooth',
         'data-filter="lager" aria-pressed="false">Clean & smooth', "filter label 1"),
        ('data-filter="strong" aria-pressed="false">Strong',
         'data-filter="strong" aria-pressed="false">Super premium', "filter label 2"),
        ('data-filter="wheat" aria-pressed="false">Wheat',
         'data-filter="wheat" aria-pressed="false">Verve', "filter label 3"),
        ('data-filter="flavour" aria-pressed="false">Flavoured',
         'data-filter="flavour" aria-pressed="false">Remix flavours', "filter label 4"),
        (f">The Kingfisher portfolio. Availability, packaging and alcohol content vary by region. "
         f"Refer to the local pack.<",
         f">The {BRAND} portfolio. Availability, packaging and alcohol content vary by region. "
         f"Refer to the local pack.<", "range note"),
        # --- pairings ---------------------------------------------------------
        ("which Kingfisher to pour with it.", f"which {BRAND} to pour with it.", "pairings intro"),
        # --- flavour feature --------------------------------------------------
        ('aria-label="Kingfisher Street Flavours"', f'aria-label="{BRAND} Remix"', "flavour aria"),
        ("<p>Lemon Masala. Mango Berry Twist.<br>Indian-inspired flavours, with the familiar "
         "bird.</p>",
         "<p>Lemongrass &amp; Ginger. Raspberry.<br>Indian-inspired flavours, naturally "
         "infused.</p>", "flavour copy"),
        # --- footer -----------------------------------------------------------
        ('<a href="#range">Our beers</a>', '<a href="#range">Our range</a>', "footer link"),
        # The credit rides along with the owner link: it sits in the same links
        # row, which already carries the footer's type styling, so it needs no
        # new CSS and keeps the pipeline to one substitution here.
        ('<a href="https://www.unitedbreweries.com/" target="_blank" rel="noopener">'
         'United Breweries \u2197</a>',
         '<a href="https://www.radicokhaitan.com/" target="_blank" rel="noopener">'
         'Radico Khaitan \u2197</a>'
         '<span class="footer-credit">Made by Saksham</span>', "footer owner link + credit"),
        ("Independent design concept. Kingfisher and product trademarks belong to their "
         "respective owners.",
         f"Independent design concept. {BRAND} and product trademarks belong to their "
         f"respective owners.", "footer legal"),
        # Accessibility label; the #beer anchor itself is left intact so the skip
        # link, the in-page nav and the scroll-spy keep working unchanged.
        (">Skip to beer details", ">Skip to product details", "skip link"),
        # The hero bottle is preloaded so the fly-in animation has no decode hitch.
        # It still pointed at the old Kingfisher asset.
        ('<link rel="preload" href="assets/strong-cut.webp" as="image">',
         '<link rel="preload" href="assets/mm-premium-grain.webp" as="image">',
         "hero preload"),
    ]
    for old, new, label in reps:
        text = sub_once(text, old, new, label)

    report_leftovers(text, "index.html")
    return text


def main() -> int:
    save("app.js", patch_app_js(load("app.js")))
    save("index.html", patch_index_html(load("index.html")))
    print("\npatched dist/app.js and dist/index.html")
    print("\nleft as-is (brand-mark tier, not selected):")
    for _, what in FLAGGED:
        print(f"  - {what}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
