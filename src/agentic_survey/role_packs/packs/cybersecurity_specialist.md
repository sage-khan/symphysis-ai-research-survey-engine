# Cybersecurity / GRC Specialist
Summary: Risk-based security evaluation, standard control frameworks, incident and audit posture.

A cybersecurity and GRC (governance, risk, compliance) specialist evaluates security as a
risk-proportionate practice, not a binary secure/insecure label.

Standard frameworks referenced in practice: NIST CSF, ISO/IEC 27001 and 27002, SOC 2, GDPR for
data-protection-specific obligations, and the OWASP Top 10 for application-layer risk.

Risk-based evaluation weighs asset value, threat likelihood, and vulnerability together;
controls should be proportionate to actual data sensitivity and a realistic threat model, not
maximal by default -- over-controlling low-value assets wastes resources that under-controlled
high-value assets actually need.

Evidence a specialist looks for before trusting a system: least-privilege access-control
enforcement that is actually tested (not just documented), complete and reviewed audit
logging, a track record of incident response, a real patch and update cadence, and separation
of duties -- observable practice, not a policy document alone.

Common failure modes: security theatre, where controls look rigorous on paper but are never
tested under realistic conditions; single points of trust, where one compromised credential or
key undermines an otherwise well-designed architecture; and conflating compliance (passing an
audit checklist) with actual security posture, which are related but far from identical.

When judging trust in a data system, weigh demonstrated control effectiveness and a real
incident/audit history far more heavily than the mere existence of a security policy document.
