"""
Dataset Bias & Coverage Analysis Module
========================================
Provides comprehensive analysis of the disease prediction model's dataset,
identifying class imbalance, underrepresented diseases/symptoms, and
per-disease performance metrics.
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from collections import Counter, defaultdict
import json
import logging
import random

logger = logging.getLogger(__name__)


class BiasAnalyzer:
    """
    Analyzes bias and coverage in the disease prediction model's dataset.
    
    Generates metrics including:
    - Class distribution across diseases
    - Symptom frequency and coverage
    - Per-disease simulated performance metrics
    - Underrepresentation flags
    """

    # Thresholds for underrepresentation
    MIN_SYMPTOMS_THRESHOLD = 4  # Diseases with fewer symptoms are flagged
    LOW_WEIGHT_THRESHOLD = 0.65  # Symptoms below this weight are considered weak
    BIAS_IMBALANCE_RATIO = 2.0  # Ratio above which class sizes are considered imbalanced

    def __init__(self, ml_model):
        self.ml_model = ml_model
        self.disease_weights = ml_model.disease_weights
        self._analysis_cache = None

    def run_full_analysis(self) -> Dict[str, Any]:
        """
        Execute a complete bias and coverage analysis. Returns a comprehensive
        result dictionary suitable for JSON serialization and dashboard display.
        """
        if self._analysis_cache:
            return self._analysis_cache

        analysis = {
            'summary': self._generate_summary(),
            'class_distribution': self._analyze_class_distribution(),
            'symptom_coverage': self._analyze_symptom_coverage(),
            'underrepresented_diseases': self._find_underrepresented_diseases(),
            'underrepresented_symptoms': self._find_underrepresented_symptoms(),
            'per_disease_metrics': self._simulate_per_disease_metrics(),
            'bias_indicators': self._compute_bias_indicators(),
            'disease_complexity': self._analyze_disease_complexity(),
            'symptom_overlap': self._analyze_symptom_overlap(),
        }

        self._analysis_cache = analysis
        return analysis

    def invalidate_cache(self):
        """Clear the cached analysis."""
        self._analysis_cache = None

    # ─── Summary ──────────────────────────────────────────────────────────

    def _generate_summary(self) -> Dict[str, Any]:
        """High-level summary statistics."""
        all_symptoms = set()
        total_symptom_slots = 0
        biases = []

        for disease, data in self.disease_weights.items():
            symptoms = data['symptoms']
            all_symptoms.update(symptoms.keys())
            total_symptom_slots += len(symptoms)
            biases.append(data['bias'])

        symptom_counts = [len(d['symptoms']) for d in self.disease_weights.values()]

        return {
            'total_diseases': len(self.disease_weights),
            'total_unique_symptoms': len(all_symptoms),
            'total_symptom_slots': total_symptom_slots,
            'avg_symptoms_per_disease': round(np.mean(symptom_counts), 2),
            'median_symptoms_per_disease': int(np.median(symptom_counts)),
            'min_symptoms': int(np.min(symptom_counts)),
            'max_symptoms': int(np.max(symptom_counts)),
            'std_symptoms': round(float(np.std(symptom_counts)), 2),
            'avg_bias': round(float(np.mean(biases)), 2),
            'bias_range': [round(float(np.min(biases)), 2), round(float(np.max(biases)), 2)],
        }

    # ─── Class Distribution ───────────────────────────────────────────────

    def _analyze_class_distribution(self) -> Dict[str, Any]:
        """
        Analyze how diseases are distributed based on symptom count and weight magnitude.
        Since the model uses hardcoded weights rather than training data, we analyze
        the 'representational complexity' as a proxy for dataset class size.
        """
        distribution = {}
        for disease, data in self.disease_weights.items():
            symptoms = data['symptoms']
            weights = list(symptoms.values())
            distribution[disease] = {
                'symptom_count': len(symptoms),
                'avg_weight': round(float(np.mean(weights)), 3),
                'max_weight': round(float(np.max(weights)), 3),
                'min_weight': round(float(np.min(weights)), 3),
                'weight_std': round(float(np.std(weights)), 3),
                'total_weight': round(float(np.sum(weights)), 3),
                'bias': data['bias'],
            }

        # Sort by symptom count for easy visualization
        sorted_dist = dict(
            sorted(distribution.items(), key=lambda x: x[1]['symptom_count'], reverse=True)
        )

        counts = [d['symptom_count'] for d in distribution.values()]
        return {
            'diseases': sorted_dist,
            'histogram': self._build_histogram(counts),
            'imbalance_ratio': round(max(counts) / max(min(counts), 1), 2),
        }

    def _build_histogram(self, values: List[int]) -> Dict[str, int]:
        """Create a histogram of symptom counts."""
        counter = Counter(values)
        return {str(k): v for k, v in sorted(counter.items())}

    # ─── Symptom Coverage ─────────────────────────────────────────────────

    def _analyze_symptom_coverage(self) -> Dict[str, Any]:
        """
        Analyze which symptoms appear across how many diseases and their average weight.
        """
        symptom_diseases = defaultdict(list)
        symptom_weights_agg = defaultdict(list)

        for disease, data in self.disease_weights.items():
            for symptom, weight in data['symptoms'].items():
                symptom_diseases[symptom].append(disease)
                symptom_weights_agg[symptom].append(weight)

        coverage = {}
        for symptom in symptom_diseases:
            coverage[symptom] = {
                'disease_count': len(symptom_diseases[symptom]),
                'diseases': symptom_diseases[symptom],
                'avg_weight': round(float(np.mean(symptom_weights_agg[symptom])), 3),
                'max_weight': round(float(np.max(symptom_weights_agg[symptom])), 3),
                'min_weight': round(float(np.min(symptom_weights_agg[symptom])), 3),
            }

        # Sort by disease_count descending (most shared symptoms first)
        sorted_coverage = dict(
            sorted(coverage.items(), key=lambda x: x[1]['disease_count'], reverse=True)
        )

        disease_counts = [c['disease_count'] for c in coverage.values()]
        return {
            'symptoms': sorted_coverage,
            'total_unique_symptoms': len(coverage),
            'shared_symptoms': sum(1 for c in coverage.values() if c['disease_count'] > 1),
            'unique_to_one_disease': sum(1 for c in coverage.values() if c['disease_count'] == 1),
            'most_shared_count': max(disease_counts) if disease_counts else 0,
        }

    # ─── Underrepresented Diseases ────────────────────────────────────────

    def _find_underrepresented_diseases(self) -> List[Dict[str, Any]]:
        """
        Identify diseases that may be underrepresented due to:
        - Very few symptoms (below MIN_SYMPTOMS_THRESHOLD)
        - All low weights
        - Extreme bias values
        """
        flagged = []
        all_symptom_counts = [len(d['symptoms']) for d in self.disease_weights.values()]
        avg_count = np.mean(all_symptom_counts)

        for disease, data in self.disease_weights.items():
            reasons = []
            symptoms = data['symptoms']
            weights = list(symptoms.values())
            count = len(symptoms)

            if count < self.MIN_SYMPTOMS_THRESHOLD:
                reasons.append(f'Very few symptoms ({count})')

            if count < avg_count * 0.6:
                reasons.append(f'Below 60% of average symptom count ({count} vs avg {avg_count:.1f})')

            avg_w = np.mean(weights)
            if avg_w < self.LOW_WEIGHT_THRESHOLD:
                reasons.append(f'Low average weight ({avg_w:.3f})')

            if data['bias'] <= -4.0:
                reasons.append(f'Very strong negative bias ({data["bias"]}), harder to diagnose')

            if reasons:
                flagged.append({
                    'disease': disease,
                    'display_name': disease.replace('_', ' ').title(),
                    'symptom_count': count,
                    'avg_weight': round(float(avg_w), 3),
                    'bias': data['bias'],
                    'reasons': reasons,
                    'severity': 'high' if len(reasons) >= 2 else 'medium',
                })

        # Sort by severity (high first), then by symptom count
        flagged.sort(key=lambda x: (0 if x['severity'] == 'high' else 1, x['symptom_count']))
        return flagged

    # ─── Underrepresented Symptoms ─────────────────────────────────────────

    def _find_underrepresented_symptoms(self) -> List[Dict[str, Any]]:
        """
        Identify symptoms that appear in only one disease or have consistently low weights.
        """
        symptom_info = defaultdict(lambda: {'diseases': [], 'weights': []})

        for disease, data in self.disease_weights.items():
            for symptom, weight in data['symptoms'].items():
                symptom_info[symptom]['diseases'].append(disease)
                symptom_info[symptom]['weights'].append(weight)

        flagged = []
        for symptom, info in symptom_info.items():
            reasons = []

            if len(info['diseases']) == 1:
                reasons.append(f'Unique to only one disease ({info["diseases"][0]})')

            avg_w = np.mean(info['weights'])
            if avg_w < self.LOW_WEIGHT_THRESHOLD:
                reasons.append(f'Low average weight ({avg_w:.3f})')

            if reasons:
                flagged.append({
                    'symptom': symptom,
                    'display_name': symptom.replace('_', ' ').title(),
                    'disease_count': len(info['diseases']),
                    'diseases': info['diseases'],
                    'avg_weight': round(float(avg_w), 3),
                    'reasons': reasons,
                })

        flagged.sort(key=lambda x: (x['disease_count'], x['avg_weight']))
        return flagged

    # ─── Per-Disease Simulated Performance Metrics ────────────────────────

    def _simulate_per_disease_metrics(self, num_simulations: int = 200) -> Dict[str, Dict]:
        """
        Simulate predictions with random symptom subsets to estimate per-disease
        performance characteristics (since we don't have a test dataset).
        
        For each disease, we simulate:
        - Positive cases: random subsets of the disease's own symptoms
        - Negative cases: random symptoms from OTHER diseases
        
        We then measure accuracy, sensitivity, specificity for each disease.
        """
        random.seed(42)  # Reproducibility
        np.random.seed(42)

        all_diseases = list(self.disease_weights.keys())
        metrics = {}

        for disease in all_diseases:
            disease_symptoms = list(self.disease_weights[disease]['symptoms'].keys())
            other_symptoms = []
            for d, data in self.disease_weights.items():
                if d != disease:
                    other_symptoms.extend(data['symptoms'].keys())
            other_symptoms = list(set(other_symptoms) - set(disease_symptoms))

            tp, fp, tn, fn = 0, 0, 0, 0
            probabilities_positive = []
            probabilities_negative = []

            # Positive cases: subsets of this disease's symptoms
            for _ in range(num_simulations):
                n_symptoms = random.randint(1, max(1, len(disease_symptoms)))
                sampled = random.sample(disease_symptoms, n_symptoms)
                result = self.ml_model.predict_disease_probability(disease, sampled)
                prob = result['raw_probability']
                probabilities_positive.append(prob)

                if prob >= 0.5:
                    tp += 1
                else:
                    fn += 1

            # Negative cases: symptoms from other diseases
            for _ in range(num_simulations):
                if other_symptoms:
                    n_symptoms = random.randint(1, min(5, len(other_symptoms)))
                    sampled = random.sample(other_symptoms, n_symptoms)
                else:
                    sampled = []

                result = self.ml_model.predict_disease_probability(disease, sampled)
                prob = result['raw_probability']
                probabilities_negative.append(prob)

                if prob < 0.5:
                    tn += 1
                else:
                    fp += 1

            total = tp + fp + tn + fn
            accuracy = (tp + tn) / total if total > 0 else 0
            sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0  # Recall
            specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            f1 = 2 * (precision * sensitivity) / (precision + sensitivity) if (precision + sensitivity) > 0 else 0

            metrics[disease] = {
                'display_name': disease.replace('_', ' ').title(),
                'accuracy': round(accuracy, 3),
                'sensitivity': round(sensitivity, 3),
                'specificity': round(specificity, 3),
                'precision': round(precision, 3),
                'f1_score': round(f1, 3),
                'true_positives': tp,
                'false_positives': fp,
                'true_negatives': tn,
                'false_negatives': fn,
                'avg_positive_probability': round(float(np.mean(probabilities_positive)), 3),
                'avg_negative_probability': round(float(np.mean(probabilities_negative)), 3),
                'symptom_count': len(disease_symptoms),
                'bias': self.disease_weights[disease]['bias'],
            }

        return metrics

    # ─── Bias Indicators ──────────────────────────────────────────────────

    def _compute_bias_indicators(self) -> Dict[str, Any]:
        """
        Compute overall bias indicators across the model.
        """
        symptom_counts = []
        weight_averages = []
        biases = []

        for disease, data in self.disease_weights.items():
            weights = list(data['symptoms'].values())
            symptom_counts.append(len(weights))
            weight_averages.append(np.mean(weights))
            biases.append(data['bias'])

        # Gini coefficient of symptom counts (measure of inequality)
        gini = self._gini_coefficient(symptom_counts)

        # Coefficient of variation
        cv = float(np.std(symptom_counts) / np.mean(symptom_counts)) if np.mean(symptom_counts) > 0 else 0

        return {
            'gini_coefficient': round(gini, 4),
            'coefficient_of_variation': round(cv, 4),
            'symptom_count_range': [int(min(symptom_counts)), int(max(symptom_counts))],
            'weight_average_range': [round(float(min(weight_averages)), 3), round(float(max(weight_averages)), 3)],
            'bias_range': [round(float(min(biases)), 2), round(float(max(biases)), 2)],
            'bias_std': round(float(np.std(biases)), 3),
            'diseases_with_few_symptoms': sum(1 for c in symptom_counts if c < self.MIN_SYMPTOMS_THRESHOLD),
            'diseases_with_extreme_bias': sum(1 for b in biases if b <= -4.0),
            'overall_balance_score': self._compute_balance_score(symptom_counts, biases),
        }

    def _gini_coefficient(self, values: List[float]) -> float:
        """Compute the Gini coefficient (0 = perfect equality, 1 = total inequality)."""
        arr = np.array(values, dtype=float)
        if arr.sum() == 0:
            return 0
        arr = np.sort(arr)
        n = len(arr)
        index = np.arange(1, n + 1)
        return float((2 * np.sum(index * arr) - (n + 1) * np.sum(arr)) / (n * np.sum(arr)))

    def _compute_balance_score(self, counts: List[int], biases: List[float]) -> Dict:
        """
        An overall 0-100 balance score for the model.
        Higher = more balanced.
        """
        # Symptom count balance (lower CV = better)
        cv = np.std(counts) / np.mean(counts) if np.mean(counts) > 0 else 1
        count_score = max(0, 100 - (cv * 100))

        # Bias balance (lower std = better)
        bias_std = np.std(biases)
        bias_score = max(0, 100 - (bias_std * 50))

        # Combined
        overall = round((count_score * 0.6 + bias_score * 0.4), 1)

        return {
            'overall': overall,
            'symptom_count_balance': round(count_score, 1),
            'bias_balance': round(bias_score, 1),
            'grade': 'A' if overall >= 80 else 'B' if overall >= 65 else 'C' if overall >= 50 else 'D',
        }

    # ─── Disease Complexity ───────────────────────────────────────────────

    def _analyze_disease_complexity(self) -> List[Dict]:
        """
        Rank diseases by diagnostic complexity based on symptom overlap with other diseases.
        """
        complexity = []
        for disease, data in self.disease_weights.items():
            my_symptoms = set(data['symptoms'].keys())
            overlap_count = 0
            overlapping_diseases = []

            for other_disease, other_data in self.disease_weights.items():
                if other_disease == disease:
                    continue
                other_symptoms = set(other_data['symptoms'].keys())
                shared = my_symptoms & other_symptoms
                if shared:
                    overlap_count += len(shared)
                    overlapping_diseases.append({
                        'disease': other_disease,
                        'shared_symptoms': list(shared),
                        'shared_count': len(shared),
                    })

            # Sort overlapping diseases by shared_count descending
            overlapping_diseases.sort(key=lambda x: x['shared_count'], reverse=True)

            complexity.append({
                'disease': disease,
                'display_name': disease.replace('_', ' ').title(),
                'total_overlap_count': overlap_count,
                'unique_symptom_ratio': round(
                    len(my_symptoms - self._get_all_other_symptoms(disease)) / len(my_symptoms), 3
                ) if my_symptoms else 0,
                'top_overlapping_diseases': overlapping_diseases[:5],
                'symptom_count': len(my_symptoms),
            })

        complexity.sort(key=lambda x: x['total_overlap_count'], reverse=True)
        return complexity

    def _get_all_other_symptoms(self, exclude_disease: str) -> set:
        """Get all symptoms from all diseases except the given one."""
        symptoms = set()
        for disease, data in self.disease_weights.items():
            if disease != exclude_disease:
                symptoms.update(data['symptoms'].keys())
        return symptoms

    # ─── Symptom Overlap Matrix ───────────────────────────────────────────

    def _analyze_symptom_overlap(self) -> Dict[str, Any]:
        """
        Create a summary of the symptom overlap between diseases.
        (Full matrix can be large, so we return top overlapping pairs.)
        """
        diseases = list(self.disease_weights.keys())
        overlapping_pairs = []

        for i in range(len(diseases)):
            for j in range(i + 1, len(diseases)):
                d1 = diseases[i]
                d2 = diseases[j]
                s1 = set(self.disease_weights[d1]['symptoms'].keys())
                s2 = set(self.disease_weights[d2]['symptoms'].keys())
                shared = s1 & s2
                if shared:
                    overlapping_pairs.append({
                        'disease_1': d1,
                        'disease_2': d2,
                        'shared_symptoms': list(shared),
                        'shared_count': len(shared),
                        'jaccard_index': round(len(shared) / len(s1 | s2), 3),
                    })

        overlapping_pairs.sort(key=lambda x: x['shared_count'], reverse=True)

        return {
            'total_overlapping_pairs': len(overlapping_pairs),
            'top_overlapping_pairs': overlapping_pairs[:20],
            'avg_shared_symptoms': round(
                np.mean([p['shared_count'] for p in overlapping_pairs]), 2
            ) if overlapping_pairs else 0,
        }


# Singleton instance — lazily created
_analyzer_instance = None

def get_analyzer():
    """Get or create the singleton BiasAnalyzer instance."""
    global _analyzer_instance
    if _analyzer_instance is None:
        from backend.models.ml_model import ml_model
        _analyzer_instance = BiasAnalyzer(ml_model)
    return _analyzer_instance
