from __future__ import annotations

from dataclasses import dataclass

@dataclass(frozen=True)
class SupplierScore:
    score: float
    tier: str

def supplier_score(row: dict) -> SupplierScore:
    binary = {
        "blind_shipping": 16,
        "private_label": 14,
        "mixed_designs": 8,
        "low_moq": 14,
        "no_inventory_model": 18,
        "sample_available": 8,
    }
    score = sum(weight for key, weight in binary.items() if bool(row.get(key)))
    score += min(float(row.get("quality_score") or 0), 10) * 0.8
    score += min(float(row.get("aesthetic_score") or 0), 10) * 0.6
    score += min(float(row.get("commercial_score") or 0), 10) * 0.4
    score += min(float(row.get("reliability_score") or 0), 10) * 0.4
    score = round(min(score, 100), 1)
    if score >= 82:
        tier = "AAA"
    elif score >= 70:
        tier = "AA"
    elif score >= 58:
        tier = "A"
    elif score >= 45:
        tier = "B"
    else:
        tier = "C"
    return SupplierScore(score, tier)

def unit_economics(product: dict) -> dict:
    supplier_price = float(product.get("supplier_price") or 0)
    retail = float(product.get("target_retail") or 0)
    shipping = float(product.get("shipping_cost") or 0)
    packaging = float(product.get("packaging_cost") or 0)
    fee_pct = float(product.get("payment_fee_pct") or 0)
    payment_fee = retail * fee_pct / 100
    landed = supplier_price + shipping + packaging + payment_fee
    contribution = retail - landed
    margin_pct = (contribution / retail * 100) if retail else 0
    return {
        "landed_cost": round(landed, 2),
        "contribution": round(contribution, 2),
        "margin_pct": round(margin_pct, 1),
    }

def launch_gate(product: dict) -> tuple[bool, list[str]]:
    missing = []
    required_flags = {
        "burn_test_pass": "burn test",
        "packaging_test_pass": "packaging test",
        "photo_approved": "approved product photography",
        "specs_verified": "verified specs",
    }
    for key, label in required_flags.items():
        if not bool(product.get(key)):
            missing.append(label)
    if product.get("sample_status") not in {"approved", "passed"}:
        missing.append("approved sample")
    econ = unit_economics(product)
    if econ["margin_pct"] < 35:
        missing.append("minimum 35% contribution margin")
    return (not missing, missing)
