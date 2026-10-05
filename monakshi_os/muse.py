from __future__ import annotations

BRAND_RULES = {
    "voice": "Indian, intimate, artisanal, restrained luxury",
    "avoid": ["mass-produced", "cheap", "handmade by us unless verified", "fake scarcity"],
    "themes": ["ritual", "light", "flowers", "festivals", "home", "gifting"],
}

def product_caption(name: str, form: str, fragrance: str = "", occasion: str = "") -> str:
    scent = f" in {fragrance}" if fragrance else ""
    moment = f" for {occasion}" if occasion else ""
    return (
        f"{name}. A small pool of light shaped by {form}{scent}{moment}. "
        "Made to sit quietly at the centre of a table, a thali, a gift, or an evening at home. "
        "House of Monakshi."
    )

def product_description(name: str, form: str, wax: str = "", wick: str = "", fragrance: str = "") -> str:
    details = []
    if fragrance:
        details.append(f"Fragrance: {fragrance}")
    if wax:
        details.append(f"Wax: {wax}")
    if wick:
        details.append(f"Wick: {wick}")
    detail_block = "\n".join(details)
    return (
        f"{name}\n\n"
        f"A decorative candle inspired by {form}. Designed for festive tables, gifting and slow evenings at home. "
        "Each launch piece should be listed only after its sample, specifications, burn performance and packaging are approved.\n\n"
        f"{detail_block}"
    ).strip()
