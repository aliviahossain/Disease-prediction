"""
Temporal Analysis Engine for Disease Prediction
Handles progression timeline tracking, vitals trend analysis, weighted recent medical events,  # noqa: E501
and dynamic survival probability calculations over time.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np


class TemporalAnalysisEngine:
    """
    Advanced engine to process sequential patient history, analyze vital trends,  # noqa: E501
    and compute dynamic survival probabilities.
    """

    # Healthy baselines for vitals
    VITALS_BASELINE = {
        "heart_rate": {
            "min": 60.0,
            "max": 100.0,
            "ideal": 70.0,
            "weight": 0.15,
        },
        "blood_pressure_systolic": {
            "min": 90.0,
            "max": 120.0,
            "ideal": 115.0,
            "weight": 0.20,
        },
        "blood_pressure_diastolic": {
            "min": 60.0,
            "max": 80.0,
            "ideal": 75.0,
            "weight": 0.15,
        },
        "blood_glucose": {
            "min": 70.0,
            "max": 100.0,
            "ideal": 85.0,
            "weight": 0.25,
        },
        "temperature": {
            "min": 36.1,
            "max": 37.2,
            "ideal": 36.6,
            "weight": 0.25,
        },
    }

    @classmethod
    def analyze_vitals(
        cls,
        heart_rate: Optional[float] = None,
        bp_systolic: Optional[float] = None,
        bp_diastolic: Optional[float] = None,
        blood_glucose: Optional[float] = None,
        temperature: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Analyze a single set of vitals, flag clinical anomalies, and compute a vitals health index (0 to 1).  # noqa: E501
        """
        analysis = {
            "flags": [],
            "metrics": {},
            "vitals_health_score": 1.0,  # 1.0 = perfect health, 0.0 = highly unstable # noqa: E501
            "summary": "Vitals are normal.",
        }

        penalties = 0.0
        total_vitals_count = 0

        # 1. Heart Rate
        if heart_rate is not None:
            total_vitals_count += 1
            hr_cfg = cls.VITALS_BASELINE["heart_rate"]
            if heart_rate > hr_cfg["max"]:
                severity = min(1.0, (heart_rate - hr_cfg["max"]) / 40.0)
                analysis["flags"].append(
                    {
                        "vital": "heart_rate",
                        "status": "Tachycardia (High)",
                        "value": heart_rate,
                        "severity": (
                            "danger" if heart_rate > 120 else "warning"
                        ),
                        "message": f"Elevated heart rate ({heart_rate} bpm). Target: 60-100 bpm.",  # noqa: E501
                    }
                )
                penalties += hr_cfg["weight"] * severity
            elif heart_rate < hr_cfg["min"]:
                severity = min(1.0, (hr_cfg["min"] - heart_rate) / 20.0)
                analysis["flags"].append(
                    {
                        "vital": "heart_rate",
                        "status": "Bradycardia (Low)",
                        "value": heart_rate,
                        "severity": "danger" if heart_rate < 50 else "warning",
                        "message": f"Low heart rate ({heart_rate} bpm). Target: 60-100 bpm.",  # noqa: E501
                    }
                )
                penalties += hr_cfg["weight"] * severity
            analysis["metrics"]["heart_rate"] = {
                "value": heart_rate,
                "status": (
                    "Normal"
                    if (hr_cfg["min"] <= heart_rate <= hr_cfg["max"])
                    else "Abnormal"
                ),
            }

        # 2. Blood Pressure
        if bp_systolic is not None and bp_diastolic is not None:
            total_vitals_count += 1
            sys_cfg = cls.VITALS_BASELINE["blood_pressure_systolic"]
            dia_cfg = cls.VITALS_BASELINE["blood_pressure_diastolic"]

            bp_status = "Normal"
            bp_severity = "success"
            bp_msg = ""

            if bp_systolic > 140 or bp_diastolic > 90:
                bp_status = "Hypertension Stage 2"
                bp_severity = "danger"
                bp_msg = f"Critically high blood pressure ({int(bp_systolic)}/{int(bp_diastolic)} mmHg)."  # noqa: E501
                penalties += (sys_cfg["weight"] + dia_cfg["weight"]) * 0.95
            elif bp_systolic > 120 or bp_diastolic > 80:
                bp_status = "Pre-hypertension"
                bp_severity = "warning"
                bp_msg = f"Elevated blood pressure ({int(bp_systolic)}/{int(bp_diastolic)} mmHg)."  # noqa: E501
                penalties += (sys_cfg["weight"] + dia_cfg["weight"]) * 0.4
            elif bp_systolic < 90 or bp_diastolic < 60:
                bp_status = "Hypotension"
                bp_severity = "warning"
                bp_msg = f"Low blood pressure ({int(bp_systolic)}/{int(bp_diastolic)} mmHg)."  # noqa: E501
                penalties += (sys_cfg["weight"] + dia_cfg["weight"]) * 0.5

            if bp_status != "Normal":
                analysis["flags"].append(
                    {
                        "vital": "blood_pressure",
                        "status": bp_status,
                        "value": f"{int(bp_systolic)}/{int(bp_diastolic)}",
                        "severity": bp_severity,
                        "message": bp_msg + " Target: < 120/80 mmHg.",
                    }
                )

            analysis["metrics"]["blood_pressure"] = {
                "systolic": bp_systolic,
                "diastolic": bp_diastolic,
                "status": bp_status,
            }

        # 3. Blood Glucose
        if blood_glucose is not None:
            total_vitals_count += 1
            glu_cfg = cls.VITALS_BASELINE["blood_glucose"]
            if blood_glucose > glu_cfg["max"]:
                severity = min(1.0, (blood_glucose - glu_cfg["max"]) / 100.0)
                analysis["flags"].append(
                    {
                        "vital": "blood_glucose",
                        "status": "Hyperglycemia (High)",
                        "value": blood_glucose,
                        "severity": (
                            "danger" if blood_glucose > 180 else "warning"
                        ),
                        "message": f"Elevated blood glucose ({blood_glucose} mg/dL). Target: 70-100 mg/dL (fasting).",  # noqa: E501
                    }
                )
                penalties += glu_cfg["weight"] * severity
            elif blood_glucose < glu_cfg["min"]:
                severity = min(1.0, (glu_cfg["min"] - blood_glucose) / 30.0)
                analysis["flags"].append(
                    {
                        "vital": "blood_glucose",
                        "status": "Hypoglycemia (Low)",
                        "value": blood_glucose,
                        "severity": (
                            "danger" if blood_glucose < 55 else "warning"
                        ),
                        "message": f"Critically low blood glucose ({blood_glucose} mg/dL). Target: 70-100 mg/dL.",  # noqa: E501
                    }
                )
                penalties += glu_cfg["weight"] * severity
            analysis["metrics"]["blood_glucose"] = {
                "value": blood_glucose,
                "status": (
                    "Normal"
                    if (glu_cfg["min"] <= blood_glucose <= glu_cfg["max"])
                    else "Abnormal"
                ),
            }

        # 4. Temperature
        if temperature is not None:
            total_vitals_count += 1
            temp_cfg = cls.VITALS_BASELINE["temperature"]
            if temperature > temp_cfg["max"]:
                severity = min(1.0, (temperature - temp_cfg["max"]) / 3.0)
                analysis["flags"].append(
                    {
                        "vital": "temperature",
                        "status": "Fever/Hyperthermia",
                        "value": temperature,
                        "severity": (
                            "danger" if temperature > 39.0 else "warning"
                        ),
                        "message": f"Elevated temperature ({temperature}°C). Indicating active infection or inflammation.",  # noqa: E501
                    }
                )
                penalties += temp_cfg["weight"] * severity
            elif temperature < temp_cfg["min"]:
                severity = min(1.0, (temp_cfg["min"] - temperature) / 2.0)
                analysis["flags"].append(
                    {
                        "vital": "temperature",
                        "status": "Hypothermia",
                        "value": temperature,
                        "severity": (
                            "danger" if temperature < 35.0 else "warning"
                        ),
                        "message": f"Low body temperature ({temperature}°C). Target: 36.1-37.2°C.",  # noqa: E501
                    }
                )
                penalties += temp_cfg["weight"] * severity
            analysis["metrics"]["temperature"] = {
                "value": temperature,
                "status": (
                    "Normal"
                    if (temp_cfg["min"] <= temperature <= temp_cfg["max"])
                    else "Abnormal"
                ),
            }

        # Adjust health score
        if total_vitals_count > 0:
            analysis["vitals_health_score"] = max(0.05, 1.0 - penalties)

        if len(analysis["flags"]) > 0:
            critical_flags = sum(
                1 for f in analysis["flags"] if f["severity"] == "danger"
            )
            if critical_flags > 0:
                analysis["summary"] = (
                    f"Warning: {critical_flags} critical vital anomaly detected! Medical assessment recommended."  # noqa: E501
                )
            else:
                analysis["summary"] = (
                    f"Alert: {len(analysis['flags'])} minor vital deviations observed. Keep tracking."  # noqa: E501
                )

        return analysis

    @classmethod
    def calculate_dynamic_survival(
        cls,
        disease_posterior: float,
        vitals_health_score: float,
        trend_factor: float = 0.0,
    ) -> float:
        """
        Calculate dynamic survival/recovery probability.

        Args:
            disease_posterior: The posterior probability of having the disease (0 to 1).  # noqa: E501
            vitals_health_score: The calculated vitals stability index (0 to 1).  # noqa: E501
            trend_factor: Positive or negative adjustment based on historical trend (-0.15 to +0.15).  # noqa: E501

        Returns:
            float: Dynamic survival probability percentage (0.0 to 100.0)
        """
        # Baseline survival is complementary to the disease posterior chance
        baseline_survival = 1.0 - disease_posterior

        # Modulate by vitals health score. If vitals are highly unstable, survival probability takes a hit # noqa: E501
        # If vitals are perfect (1.0), it reaches baseline or slightly better.
        vitals_modifier = (
            vitals_health_score - 0.7
        ) * 0.25  # -0.175 to +0.075 range

        # Calculate dynamic survival
        dynamic_survival = baseline_survival + vitals_modifier + trend_factor

        # Apply strict logical bounds [0.01, 0.99]
        dynamic_survival = max(0.01, min(0.99, dynamic_survival))

        return round(dynamic_survival * 100, 2)

    @classmethod
    def analyze_history_trends(
        cls, history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Process user's chronological prediction history, calculating:
        1. progression timeline with timestamps
        2. vitals trend progression (lists of values for graphing)
        3. weighted recent medical events impact
        4. dynamic survival probability updates over time

        Args:
            history: Chronologically sorted prediction records (oldest first).
        """
        if not history:
            return {
                "timeline": [],
                "vitals_trends": {},
                "recent_event_weights": [],
                "overall_trend": "stable",
                "overall_message": "No historical data to establish a trend line.",  # noqa: E501
            }

        # Sort history to be absolutely sure of chronological order (oldest first) # noqa: E501
        sorted_history = sorted(
            history,
            key=lambda x: x.get("created_at") or datetime.utcnow().isoformat(),
        )

        n_records = len(sorted_history)
        timeline = []

        vitals_trends = {
            "dates": [],
            "heart_rate": [],
            "bp_systolic": [],
            "bp_diastolic": [],
            "blood_glucose": [],
            "temperature": [],
            "survival_probability": [],
            "ml_probability": [],
        }

        # 1. Progression Timeline & Dynamic Survival Calculation
        prev_vitals_health = None
        for idx, record in enumerate(sorted_history):
            date_str = record.get("created_at")
            try:
                date_formatted = datetime.fromisoformat(date_str).strftime(
                    "%Y-%m-%d %H:%M"
                )
            except Exception:
                date_formatted = date_str

            # Analyze vitals for this record
            vitals_analysis = cls.analyze_vitals(
                heart_rate=record.get("heart_rate"),
                bp_systolic=record.get("blood_pressure_systolic"),
                bp_diastolic=record.get("blood_pressure_diastolic"),
                blood_glucose=record.get("blood_glucose"),
                temperature=record.get("temperature"),
            )

            # Trend Factor calculation: Are vitals improving compared to the previous record? # noqa: E501
            trend_factor = 0.0
            if prev_vitals_health is not None:
                current_health = vitals_analysis["vitals_health_score"]
                diff = current_health - prev_vitals_health
                # Bonus if improving, penalty if worsening
                trend_factor = np.clip(diff * 0.3, -0.15, 0.15)

            prev_vitals_health = vitals_analysis["vitals_health_score"]

            # Dynamic Survival Probability
            posterior = record.get("bayesian_posterior") or (
                record.get("ml_probability") or 0.0
            )

            # Check if record already has a calculated survival_probability, otherwise calculate it dynamically # noqa: E501
            survival_prob = record.get("survival_probability")
            if survival_prob is None:
                survival_prob = cls.calculate_dynamic_survival(
                    disease_posterior=posterior,
                    vitals_health_score=vitals_analysis["vitals_health_score"],
                    trend_factor=trend_factor,
                )

            # Update record values (optional, in-memory)
            record["survival_probability"] = survival_prob

            # Append timeline point
            timeline.append(
                {
                    "id": record.get("id"),
                    "date": date_formatted,
                    "disease": record.get("disease", "Unknown")
                    .replace("_", " ")
                    .title(),
                    "ml_probability": round(
                        (record.get("ml_probability") or 0.0) * 100, 1
                    ),
                    "bayesian_posterior": (
                        round(posterior * 100, 1)
                        if record.get("bayesian_posterior")
                        else None
                    ),
                    "survival_probability": survival_prob,
                    "risk_level": record.get(
                        "risk_level", "medium"
                    ).capitalize(),
                    "vitals_summary": vitals_analysis["summary"],
                    "flags": vitals_analysis["flags"],
                    "health_index": round(
                        vitals_analysis["vitals_health_score"] * 100, 1
                    ),
                    "vitals": {
                        "heart_rate": record.get("heart_rate"),
                        "blood_pressure": (
                            f"{record.get('blood_pressure_systolic')}/{record.get('blood_pressure_diastolic')}"  # noqa: E501
                            if record.get("blood_pressure_systolic")
                            else None
                        ),
                        "blood_glucose": record.get("blood_glucose"),
                        "temperature": record.get("temperature"),
                    },
                }
            )

            # Append to trend lists
            vitals_trends["dates"].append(date_formatted)
            vitals_trends["heart_rate"].append(record.get("heart_rate"))
            vitals_trends["bp_systolic"].append(
                record.get("blood_pressure_systolic")
            )
            vitals_trends["bp_diastolic"].append(
                record.get("blood_pressure_diastolic")
            )
            vitals_trends["blood_glucose"].append(record.get("blood_glucose"))
            vitals_trends["temperature"].append(record.get("temperature"))
            vitals_trends["survival_probability"].append(survival_prob)
            vitals_trends["ml_probability"].append(
                round((record.get("ml_probability") or 0.0) * 100, 1)
            )

        # 2. Weighted Recent Medical Events (Exponential Time Decay)
        # More recent events have higher impact weights in our summary
        recent_event_weights = []
        for idx in range(n_records):
            # Recency index: 0 is oldest, n_records-1 is latest
            # Decay factor of 0.7 per step back in time
            weight = float(0.7 ** (n_records - 1 - idx))
            recent_event_weights.append(
                {
                    "timeline_index": idx,
                    "disease": timeline[idx]["disease"],
                    "date": timeline[idx]["date"],
                    "weight": round(weight * 100, 1),
                    "health_index": timeline[idx]["health_index"],
                }
            )

        # 3. Overall progression direction
        overall_trend = "stable"
        overall_message = (
            "Your health patterns are stable and holding consistent."
        )

        if n_records >= 2:
            first_survival = timeline[0]["survival_probability"]
            latest_survival = timeline[-1]["survival_probability"]
            net_change = latest_survival - first_survival

            if net_change > 5.0:
                overall_trend = "improving"
                overall_message = f"Significant clinical improvement detected! Your recovery/survival probability has increased by {net_change:.1f}% over the last {n_records} sessions."  # noqa: E501
            elif net_change < -5.0:
                overall_trend = "worsening"
                overall_message = f"Warning: Clinical progression observed. Your dynamic survival probability has dropped by {abs(net_change):.1f}% since baseline. Consider contacting your physician."  # noqa: E501
            else:
                overall_trend = "stable"
                overall_message = "Your health status is stable. Minor fluctuations observed in vitals, but overall prognosis is steady."  # noqa: E501

        # Prepare compatible structures for JS frontend
        dates = vitals_trends["dates"]
        heart_rates = vitals_trends["heart_rate"]
        blood_glucose = vitals_trends["blood_glucose"]
        temperatures = vitals_trends["temperature"]
        systolic_bp = vitals_trends["bp_systolic"]
        diastolic_bp = vitals_trends["bp_diastolic"]

        # In JS, survival_probability values are multiplied by 100, so they must be in range 0.0 to 1.0 # noqa: E501
        survival_probability_fractions = [
            float(v) / 100.0 for v in vitals_trends["survival_probability"]
        ]

        # disease_history
        disease_history = [t["disease"] for t in timeline]

        # latest health score (0.0 to 1.0)
        latest_vitals_score = (
            float(timeline[-1]["health_index"]) / 100.0 if timeline else 1.0
        )

        # time_decay_weights matching JS format
        time_decay_weights = []
        for item in recent_event_weights:
            time_decay_weights.append(
                {
                    "disease": item["disease"],
                    "date": item["date"],
                    "weight": float(item["weight"]) / 100.0,
                    "health_index": float(item["health_index"]) / 100.0,
                }
            )

        return {
            # JS format keys
            "dates": dates,
            "vitals_health_score": latest_vitals_score,
            "clinical_direction": overall_trend,
            "time_decay_weights": time_decay_weights,
            "heart_rates": heart_rates,
            "blood_glucose": blood_glucose,
            "temperatures": temperatures,
            "systolic_bp": systolic_bp,
            "diastolic_bp": diastolic_bp,
            "survival_probability": survival_probability_fractions,
            "disease_history": disease_history,
            # Original python format keys for safety
            "timeline": timeline,
            "vitals_trends": vitals_trends,
            "recent_event_weights": recent_event_weights,
            "overall_trend": overall_trend,
            "overall_message": overall_message,
            "latest_survival_probability": (
                timeline[-1]["survival_probability"] if timeline else 100.0
            ),
            "latest_health_index": (
                timeline[-1]["health_index"] if timeline else 100.0
            ),
        }
