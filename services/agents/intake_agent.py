
def intake_agent(profile):

    # to show whether intake_agent is running in WEB UI  
    print("INTAKE AGENT IS RUNNING!")
    print("RECEIVED PROFILE:", profile)

    # 1. Define mandatory fields
    required_fields = [
        "system_name",
        "owner",
        "purpose"
    ]

    # 2. Define all expected fields
    expected_fields = [
        "system_name",
        "owner",
        "purpose",
        "scenario_description",
        "industry",
        "model_type",
        "deployment",
        "personal_data",
        "public_access",
        "human_oversight",
        "sensitive_decisions",
        "third_party_api",
        "data_sensitivity",
        "authentication",
        "data_storage",
        "privacy_controls",
        "retention_policy"
    ]

    # 3. Check mandatory fields
    missing_fields = []

    for field in required_fields:
        value = profile.get(field, "")

        if not str(value).strip():
            missing_fields.append(field)

    if missing_fields:
        raise ValueError(
            "Missing required information: "
            + ", ".join(missing_fields)
        )

    # 4. Standardise the system profile
    validated_profile = {}

    for field in expected_fields:
        value = profile.get(field, "Not sure")

        if value is None or not str(value).strip():
            value = "Not sure"

        validated_profile[field] = value

    # 5. Identify uncertain answers
    uncertain_fields = []

    for field in expected_fields:
        if validated_profile[field] == "Not sure":
            uncertain_fields.append(field)

    # 6. Return the results
    return {
        "profile": validated_profile,
        "missing_fields": missing_fields,
        "uncertain_fields": uncertain_fields,
        "intake_status": "Completed"
    }

