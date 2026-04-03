import pytest
from app.services.recommender import categorize_risk_level, recommend_products

def test_categorize_risk_level():
    assert categorize_risk_level("High") == "aggressive"
    assert categorize_risk_level("Medium") == "moderate"
    assert categorize_risk_level("Low") == "low_risk"
    assert categorize_risk_level(None) == "low_risk"
    assert categorize_risk_level(123) == "low_risk"

def test_recommend_products_empty():
    res = recommend_products({}, [])
    assert res == {"aggressive": [], "moderate": [], "low_risk": []}

def test_recommend_products_basic():
    customer = {
        "personal_details": {"kyc_status": {"uk_resident": True, "identity_verified": True}},
        "financial_profile": {"employment_type": "full-time", "disposable_income_after_debts": 1000},
        "risk_profile": {"risk_tolerance": "high"},
        "product_eligibility": {"age_eligibility_met": True},
        "regulatory_compliance": {"fca_suitability_assessment": True, "mifid_ii_compliance": True},
        "financial_goals": {"timeline": "long-term"}
    }
    
    products = [
        {
            "productId": "p1",
            "productName": "High Risk Fund",
            "riskLevel": "High",
            "requiredRiskTolerance": ["high"],
            "applicabilityRules": {"applicableCustomerTypes": ["full-time"]}
        }
    ]
    
    res = recommend_products(customer, products)
    assert len(res["aggressive"]) == 1
    assert res["aggressive"][0]["score"] > 80
    assert "Meets all major criteria" in res["aggressive"][0]["reasoning"]

def test_recommend_products_exclusion():
    customer = {
        "product_offerings": {"existing_products": ["Owned Fund"]}
    }
    products = [{"productName": "Owned Fund"}]
    res = recommend_products(customer, products)
    assert len(res["low_risk"]) == 0

def test_recommend_products_low_income():
    customer = {
        "financial_profile": {"disposable_income_after_debts": 100}
    }
    products = [{"productName": "Any Fund", "riskLevel": "Low"}]
    res = recommend_products(customer, products)
    # Score should be low but we check if reason is added
    # (Default score is 20 for non-duplicate)
    # (High disposable income (+10) is missed)
    assert len(res["low_risk"]) == 0 # below 50 threshold
