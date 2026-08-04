# Structural health monitoring and trustworthy digital twins

Real, catalogued sources relevant to Criticality (C), Verification
Strength (V), and Independent Confirmation (IC), from the structural
monitoring and digital-twin literature. Drawn from
the author's TrustRouter research literature review catalogue.

## Trustworthy Digital Twins in the Industrial Internet of Things With Blockchain, Suhail, Hussain, Khan, and Choi, 2020

Examines how blockchain can anchor trust in industrial digital twins,
where a digital twin's usefulness depends entirely on whether its
underlying sensor data can be trusted to represent the physical asset's
real state. Directly relevant to Criticality (C): a structural digital
twin (e.g. for a wind turbine foundation or a building's load-bearing
elements) is exactly the kind of data where "how big is the impact if it
is wrong" is highest, a corrupted structural reading could mean a missed
failure precursor. Also relevant to Verification Strength: the paper
discusses cryptographic anchoring of sensor provenance as the mechanism
that makes a digital twin's data trustworthy in the first place.

## Blockchain-Based Digital Twins: Research Trends, Issues, and Future Challenges, Suhail et al., 2021

A broader survey of blockchain-digital-twin integration across industrial
domains, cataloguing open research issues including trust establishment,
data provenance, and the computational overhead of on-chain verification
for high-frequency sensor streams. Relevant to Independent Confirmation
(IC): the paper discusses multi-sensor and multi-party validation schemes
for digital twins as a way to catch a single faulty or tampered sensor
before its reading is trusted, precisely what IC scores for a structural
monitoring data item.

## Anomaly Detection for Monitoring the Health of Wind Onshore and Offshore Turbine Foundations, Prowell (Onyx Insight), 2023

Practitioner-oriented work on anomaly detection specifically for wind
turbine foundation structural health, the same asset class (turbine
foundations, structural sensors) this project's own wind-energy TrustRouter
application targets. Useful grounding for Criticality (C) and Quality (Q)
scoring: a foundation-health anomaly reading has both high consequence-of-
error (structural failure risk) and specific data-quality failure modes
(sensor drift, missed anomaly windows) that a generic trust framework
needs to be calibrated against.
