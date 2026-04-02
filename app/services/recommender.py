def categorize_risk_level(risk):
    if isinstance(risk, str):
        risk_lower = risk.lower()
        if risk_lower == "high":
            return "aggressive"
        elif risk_lower == "medium":
            return "moderate"
        else:
            return "low_risk"
    return "low_risk"


def recommend_products(customer, products, min_score_threshold=50):
    recommendations = {"aggressive": [], "moderate": [], "low_risk": []}

    if not products:
        return recommendations

    for product in products:
        score = 0
        reasons = []

        category = categorize_risk_level(product.get("riskLevel", "low"))

        # Ensure product_offerings and existing_products exist and are iterable
        if (
            customer.get("product_offerings")
            and isinstance(customer["product_offerings"].get("existing_products"), list)
            and product.get("productName") in customer["product_offerings"]["existing_products"]
        ):
            continue

        # Ensure all necessary keys exist and handle potential None values
        if (
            customer.get("product_eligibility", {}).get("age_eligibility_met")
            and customer.get("personal_details", {}).get("kyc_status", {}).get("uk_resident")
            and customer.get("financial_profile", {}).get("employment_type")
            in product.get("applicabilityRules", {}).get("applicableCustomerTypes", [])
        ):
            score += 15

        if customer.get("risk_profile", {}).get("risk_tolerance") in product.get(
            "requiredRiskTolerance", []
        ):
            score += 20
        else:
            reasons.append("Risk tolerance does not match")

        if (
            customer.get("personal_details", {}).get("kyc_status", {}).get("identity_verified")
            and customer.get("regulatory_compliance", {}).get("fca_suitability_assessment")
            and customer.get("regulatory_compliance", {}).get("mifid_ii_compliance")
        ):
            score += 15

        if product.get("applicabilityRules", {}).get(
            "openBankingRequired"
        ) and "open_banking_data" in customer.get("financial_profile", {}):
            score += 10

        if customer.get("financial_profile", {}).get("disposable_income_after_debts", 0) >= 500:
            score += 10
        else:
            reasons.append("Low disposable income")

        if customer.get("financial_goals", {}).get("timeline", "").lower() == "long-term":
            score += 10

        score += 20  # Not a duplicate product

        if score >= min_score_threshold:
            recommendations[category].append(
                {
                    "productId": product.get("productId"),
                    "productName": product.get("productName"),
                    "score": score,
                    "confidence": f"{score}%",
                    "reasoning": reasons if reasons else ["Meets all major criteria"],
                }
            )

    return recommendations
