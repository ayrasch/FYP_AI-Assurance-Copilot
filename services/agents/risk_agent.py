
def risk_agent(profile, mapped_controls):


    # 1. Prepare risk findings
    findings = []

    # 2. Check whether personal data is involved
    if profile.get("personal_data") == "Yes":
        findings.append({
            "risk": "Personal Data Exposure",
            "description": (
                "The AI system processes personal data, "
                "which may be exposed or misused."
            ),
            "severity": "High",
            "recommendation": (
                "Implement data protection measures and "
                "restrict access to personal information."
            )
        })

    # 3. Check whether the system is publicly accessible
    if profile.get("public_access") == "Yes":
        findings.append({
            "risk": "Unauthorised Access",
            "description": (
                "The AI system is publicly accessible and "
                "may be exposed to unauthorised access."
            ),
            "severity": "High",
            "recommendation": (
                "Implement authentication and access controls."
            )
        })

    # 4. Check whether a third-party API is used
    if profile.get("third_party_api") == "Yes":
        findings.append({
            "risk": "Third-Party Security Risk",
            "description": (
                "The AI system uses an external API, "
                "which may introduce third-party security risks."
            ),
            "severity": "Medium",
            "recommendation": (
                "Review the third-party provider's security "
                "measures and data handling practices."
            )
        })

    # 5. Check whether human oversight is available
    if profile.get("human_oversight") == "No":
        findings.append({
            "risk": "Lack of Human Oversight",
            "description": (
                "The AI system operates without human oversight, "
                "which may result in unchecked AI decisions."
            ),
            "severity": "High",
            "recommendation": (
                "Introduce human review for important AI decisions."
            )
        })

    # 6. Return risk assessment results
    print("RISK AGENT IS RUNNING!")
    print("Number of risks identified:", len(findings))

    return {
        "risk_status": "BASIC_ASSESSMENT",
        "findings": findings,
        "total_risks": len(findings),
        "source_verified": False
    }

