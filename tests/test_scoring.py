from monakshi_os.scoring import launch_gate, supplier_score, unit_economics

def test_supplier_score_rewards_operational_fit():
    s = {
        "blind_shipping": 1,
        "private_label": 1,
        "mixed_designs": 1,
        "low_moq": 1,
        "no_inventory_model": 1,
        "sample_available": 1,
        "quality_score": 9,
        "aesthetic_score": 9,
        "commercial_score": 8,
        "reliability_score": 8,
    }
    result = supplier_score(s)
    assert result.tier == "AAA"
    assert result.score >= 82

def test_product_cannot_launch_without_physical_gates():
    p = {
        "supplier_price": 180,
        "target_retail": 499,
        "shipping_cost": 60,
        "packaging_cost": 20,
        "payment_fee_pct": 2,
        "sample_status": "approved",
        "burn_test_pass": 0,
        "packaging_test_pass": 1,
        "photo_approved": 1,
        "specs_verified": 1,
    }
    passed, missing = launch_gate(p)
    assert not passed
    assert "burn test" in missing
    assert unit_economics(p)["margin_pct"] > 35
