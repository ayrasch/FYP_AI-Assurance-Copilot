
from services.agents.intake_agent import intake_agent
from services.agents.mapping_agent import mapping_agent
from services.agents.risk_agent import risk_agent
from services.agents.documentation_agent import documentation_agent

import inspect

print("RISK AGENT FILE:")
print(inspect.getfile(risk_agent))

print("RISK AGENT PARAMETERS:")
print(inspect.signature(risk_agent))


def assess(profile):

    # Agent 1: Intake
    intake_result = intake_agent(profile)

    validated_profile = intake_result["profile"]

    # Agent 2: Mapping / RAG
    mapped_controls = mapping_agent(validated_profile)

    # Agent 3: Risk Assessment
    risk_findings = risk_agent(
        validated_profile,
        mapped_controls
    )

    # Agent 4: Documentation
    report = documentation_agent(
        validated_profile,
        mapped_controls,
        risk_findings
    )

    return report, "DRAFT"
