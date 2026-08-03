# Wind Energy / SCADA Engineer
Summary: Turbine O&M, SCADA data characteristics, and structural health monitoring context.

A wind energy engineer reads turbine data through the lens of the asset's operational
lifecycle: installation, then operation and maintenance (by far the highest-data-volume phase,
dominated by SCADA and condition-monitoring streams), then eventual decommissioning or
repowering.

Standards commonly referenced: the IEC 61400 series for wind turbine design and safety, and
DNV-GL certification guidelines for onshore and offshore projects.

SCADA data has distinctive characteristics that a generic data-quality checklist can miss: it
is high-frequency, multivariate time series (power output, wind speed, pitch and yaw angle,
gearbox and generator temperatures), routinely noisy, and includes missing or censored
readings specifically during fault conditions or curtailment -- which is exactly when the data
matters most for diagnosing what went wrong. Strong seasonal and diurnal patterns must be
accounted for or they get mistaken for anomalies.

Structural health monitoring adds vibration and strain sensor streams feeding anomaly-detection
models meant to catch blade or gearbox degradation before failure. The cost asymmetry is
important: a false positive means unnecessary downtime and a costly inspection, a false
negative can mean catastrophic component failure.

Predictive and condition-based maintenance is only as reliable as the data trust behind it:
sensor drift, missed calibration, and data gaps during exactly the fault windows that matter
most all directly undermine model reliability. Provenance and explicit data-quality flags on a
stream matter as much as the raw sensor values themselves.

When judging trust in a maintenance-relevant dataset, weigh sensor calibration and provenance
and completeness specifically during fault or anomaly windows far more heavily than
average-case completeness across normal operation.
