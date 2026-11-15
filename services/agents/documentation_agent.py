
def documentation_agent(profile, mapped_controls, risk_result):

    # 1. Retrieve AI system information
    system_name = profile.get("system_name", "Not provided")
    owner = profile.get("owner", "Not provided")
    purpose = profile.get("purpose", "Not provided")
    scenario = profile.get(
        "scenario_description",
        "Not provided"
    )

    # 2. Retrieve mapping results
    controls = mapped_controls.get("mapped_controls", [])
    mapping_status = mapped_controls.get(
        "mapping_status",
        "NOT_CONNECTED"
    )

    # 3. Retrieve risk assessment results
    findings = risk_result.get("findings", [])
    risk_status = risk_result.get(
        "risk_status",
        "NOT_COMPLETED"
    )

    total_risks = len(findings)

    # 4. Prepare the assessment summary
    summary = (
        "The AI assurance assessment for "
        + system_name
        + " has been processed. "
        + "A total of "
        + str(total_risks)
        + " potential risks were identified. "
        + "Control mapping and source verification "
        + "are still under development."
    )

    # 5. Prepare the final report
    report = {
        "system_name": system_name,
        "owner": owner,
        "purpose": purpose,
        "scenario_description": scenario,
        "summary": summary,
        "mapped_controls": controls,
        "findings": findings,
        "total_risks": total_risks,
        "mapping_status": mapping_status,
        "risk_status": risk_status,
        "source_verified": False,
        "report_status": "DRAFT"
    }

    # 6. Return the report
    print("DOCUMENTATION AGENT IS RUNNING!")
    print("Assessment report generated for:", system_name)

    return report

