import numpy as np
from typing import List, Dict, Tuple
import json
import logging

logger = logging.getLogger(__name__)

class DiseaseMLModel:
    """
    Machine Learning model for disease prediction based on symptoms.
    Uses logistic regression-style weighted scoring.
    """
    
    def __init__(self):
        # Symptom weights for each disease (trained coefficients)
        self.disease_weights = {
            'diabetes': {'symptoms': {'increased_thirst': 0.85, 'frequent_urination': 0.90, 'extreme_hunger': 0.75, 'unexplained_weight_loss': 0.80, 'fatigue': 0.60, 'blurred_vision': 0.70, 'slow_healing_sores': 0.65, 'frequent_infections': 0.60, 'tingling_hands_feet': 0.70, 'darkened_skin': 0.55}, 'bias': -2.5},
            'hypertension': {'symptoms': {'severe_headache': 0.75, 'chest_pain': 0.85, 'difficulty_breathing': 0.80, 'irregular_heartbeat': 0.90, 'blood_in_urine': 0.70, 'pounding_sensation': 0.65, 'vision_problems': 0.60, 'fatigue': 0.50, 'dizziness': 0.70, 'nosebleeds': 0.55}, 'bias': -2.8},
            'covid19': {'symptoms': {'fever': 0.80, 'dry_cough': 0.85, 'fatigue': 0.70, 'loss_taste_smell': 0.95, 'sore_throat': 0.60, 'headache': 0.65, 'body_aches': 0.70, 'difficulty_breathing': 0.90, 'chest_pain': 0.75, 'confusion': 0.80}, 'bias': -3.0},
            'heart_disease': {'symptoms': {'chest_pain': 0.90, 'shortness_breath': 0.85, 'pain_arms_neck': 0.75, 'dizziness': 0.65, 'rapid_heartbeat': 0.80, 'fatigue': 0.60, 'swelling_legs': 0.70, 'cold_sweats': 0.75, 'nausea': 0.55, 'jaw_pain': 0.70}, 'bias': -2.7},
            
            # --- Expanded CSV Diseases ---
            'influenza': {'symptoms': {'fever': 0.85, 'chills': 0.80, 'muscle_aches': 0.85, 'cough': 0.75, 'congestion': 0.70, 'runny_nose': 0.70, 'headache': 0.75, 'fatigue': 0.80}, 'bias': -2.0},
            'malaria': {'symptoms': {'fever': 0.90, 'chills': 0.90, 'headache': 0.75, 'nausea': 0.70, 'vomiting': 0.70, 'muscle_pain': 0.80, 'fatigue': 0.75, 'sweating': 0.85}, 'bias': -2.2},
            'diabetes_type_2': {'symptoms': {'increased_thirst': 0.85, 'frequent_urination': 0.90, 'hunger': 0.75, 'fatigue': 0.70, 'blurred_vision': 0.65}, 'bias': -2.5},
            'breast_cancer': {'symptoms': {'breast_lump': 0.95, 'breast_pain': 0.70, 'nipple_discharge': 0.80, 'skin_changes': 0.75, 'swollen_lymph_nodes': 0.70}, 'bias': -4.0},
            'lung_cancer': {'symptoms': {'persistent_cough': 0.90, 'coughing_blood': 0.95, 'chest_pain': 0.80, 'shortness_breath': 0.85, 'weight_loss': 0.75}, 'bias': -4.0},
            'colorectal_cancer': {'symptoms': {'change_bowel_habits': 0.85, 'blood_in_stool': 0.95, 'abdominal_pain': 0.75, 'weight_loss': 0.70, 'fatigue': 0.65}, 'bias': -4.0},
            'prostate_cancer': {'symptoms': {'difficulty_urinating': 0.85, 'blood_in_urine': 0.90, 'pelvic_pain': 0.70, 'bone_pain': 0.60}, 'bias': -4.0},
            'stroke': {'symptoms': {'numbness_face_arm_leg': 0.95, 'confusion': 0.90, 'trouble_speaking': 0.95, 'trouble_seeing': 0.85, 'severe_headache': 0.80, 'dizziness': 0.75}, 'bias': -3.0},
            'pneumonia': {'symptoms': {'cough_phlegm': 0.90, 'fever': 0.85, 'chills': 0.80, 'difficulty_breathing': 0.90, 'chest_pain': 0.85, 'fatigue': 0.75}, 'bias': -2.5},
            'tuberculosis': {'symptoms': {'persistent_cough': 0.90, 'coughing_blood': 0.95, 'chest_pain': 0.75, 'fever': 0.70, 'night_sweats': 0.85, 'weight_loss': 0.80}, 'bias': -3.0},
            'hepatitis_b': {'symptoms': {'yellow_skin_eyes': 0.95, 'dark_urine': 0.85, 'fatigue': 0.80, 'nausea': 0.75, 'abdominal_pain': 0.70}, 'bias': -3.0},
            'hepatitis_c': {'symptoms': {'yellow_skin_eyes': 0.90, 'dark_urine': 0.80, 'fatigue': 0.85, 'loss_appetite': 0.75, 'nausea': 0.70}, 'bias': -3.0},
            'hiv_aids': {'symptoms': {'fever': 0.80, 'chills': 0.75, 'rash': 0.70, 'night_sweats': 0.85, 'muscle_aches': 0.75, 'sore_throat': 0.70, 'swollen_lymph_nodes': 0.90}, 'bias': -3.5},
            'alzheimers_disease': {'symptoms': {'memory_loss': 0.95, 'difficulty_planning': 0.85, 'confusion_time_place': 0.90, 'misplacing_items': 0.80, 'mood_changes': 0.75}, 'bias': -3.5},
            'parkinsons_disease': {'symptoms': {'tremor': 0.95, 'slowed_movement': 0.90, 'rigid_muscles': 0.85, 'impaired_posture': 0.80, 'loss_automatic_movements': 0.75}, 'bias': -3.5},
            'multiple_sclerosis': {'symptoms': {'numbness_weakness': 0.90, 'vision_problems': 0.85, 'tingling': 0.80, 'fatigue': 0.85, 'dizziness': 0.75}, 'bias': -3.5},
            'epilepsy': {'symptoms': {'seizures': 0.99, 'confusion': 0.75, 'staring_spell': 0.80, 'uncontrollable_jerking': 0.90, 'loss_consciousness': 0.85}, 'bias': -3.0},
            'asthma': {'symptoms': {'shortness_breath': 0.90, 'chest_tightness': 0.85, 'wheezing': 0.95, 'coughing_at_night': 0.80}, 'bias': -2.5},
            'copd': {'symptoms': {'shortness_breath': 0.90, 'wheezing': 0.85, 'chest_tightness': 0.80, 'chronic_cough': 0.90, 'frequent_infections': 0.75}, 'bias': -2.8},
            'kidney_disease': {'symptoms': {'fatigue': 0.80, 'swollen_ankles': 0.85, 'poor_appetite': 0.75, 'puffy_eyes': 0.70, 'frequent_urination': 0.80}, 'bias': -3.0},
            'liver_disease': {'symptoms': {'yellow_skin_eyes': 0.95, 'abdominal_pain': 0.80, 'swelling_legs': 0.75, 'dark_urine': 0.85, 'chronic_fatigue': 0.80}, 'bias': -3.0},
            'osteoarthritis': {'symptoms': {'joint_pain': 0.90, 'stiffness': 0.85, 'tenderness': 0.80, 'loss_flexibility': 0.75, 'grating_sensation': 0.70}, 'bias': -2.5},
            'rheumatoid_arthritis': {'symptoms': {'tender_joints': 0.90, 'joint_stiffness': 0.90, 'fatigue': 0.80, 'fever': 0.60, 'loss_appetite': 0.70}, 'bias': -3.0},
            'osteoporosis': {'symptoms': {'back_pain': 0.80, 'loss_height': 0.85, 'stooped_posture': 0.80, 'bone_fracture': 0.90}, 'bias': -2.8},
            'migraine': {'symptoms': {'severe_headache': 0.95, 'sensitivity_light': 0.90, 'sensitivity_sound': 0.85, 'nausea': 0.80, 'vomiting': 0.75}, 'bias': -2.0},
            'depression': {'symptoms': {'persistent_sadness': 0.95, 'loss_interest': 0.90, 'sleep_disturbances': 0.85, 'fatigue': 0.80, 'anxiety': 0.75}, 'bias': -2.5},
            'anxiety_disorder': {'symptoms': {'nervousness': 0.90, 'panic': 0.85, 'rapid_heartbeat': 0.80, 'trembling': 0.75, 'fatigue': 0.70}, 'bias': -2.5},
            'bipolar_disorder': {'symptoms': {'mood_swings': 0.95, 'high_energy': 0.90, 'low_energy': 0.90, 'sleep_problems': 0.80}, 'bias': -3.0},
            'schizophrenia': {'symptoms': {'delusions': 0.95, 'hallucinations': 0.95, 'disorganized_speech': 0.90, 'abnormal_behavior': 0.85}, 'bias': -3.5},
            'celiac_disease': {'symptoms': {'diarrhea': 0.90, 'fatigue': 0.85, 'weight_loss': 0.80, 'bloating': 0.85, 'abdominal_pain': 0.80}, 'bias': -3.0},
            'crohns_disease': {'symptoms': {'diarrhea': 0.90, 'fever': 0.75, 'fatigue': 0.80, 'abdominal_pain': 0.85, 'blood_in_stool': 0.80}, 'bias': -3.0},
            'ulcerative_colitis': {'symptoms': {'diarrhea_blood': 0.95, 'abdominal_pain': 0.85, 'rectal_pain': 0.80, 'weight_loss': 0.75, 'fatigue': 0.70}, 'bias': -3.0},
            'gout': {'symptoms': {'intense_joint_pain': 0.95, 'lingering_discomfort': 0.80, 'inflammation': 0.85, 'limited_range_motion': 0.75}, 'bias': -2.5},
            'psoriasis': {'symptoms': {'red_patches_skin': 0.95, 'scaling_spots': 0.90, 'dry_cracked_skin': 0.80, 'itching': 0.75, 'swollen_joints': 0.70}, 'bias': -2.5},
            'lupus': {'symptoms': {'fatigue': 0.90, 'joint_pain': 0.85, 'butterfly_rash': 0.95, 'fever': 0.75, 'sensitivity_light': 0.80}, 'bias': -3.5},
            'fibromyalgia': {'symptoms': {'widespread_pain': 0.95, 'fatigue': 0.90, 'cognitive_difficulties': 0.80, 'sleep_problems': 0.85}, 'bias': -3.0},
            'iron_deficiency_anemia': {'symptoms': {'extreme_fatigue': 0.90, 'weakness': 0.85, 'pale_skin': 0.80, 'chest_pain': 0.75, 'cold_hands_feet': 0.70}, 'bias': -2.5},
            'vitamin_d_deficiency': {'symptoms': {'fatigue': 0.80, 'bone_pain': 0.85, 'muscle_weakness': 0.80, 'mood_changes': 0.70}, 'bias': -2.0},
            'hypothyroidism': {'symptoms': {'fatigue': 0.90, 'increased_sensitivity_cold': 0.85, 'constipation': 0.80, 'dry_skin': 0.75, 'weight_gain': 0.80}, 'bias': -2.5},
            'hyperthyroidism': {'symptoms': {'unintentional_weight_loss': 0.90, 'rapid_heartbeat': 0.85, 'increased_appetite': 0.80, 'nervousness': 0.80, 'sweating': 0.75}, 'bias': -2.5},
            'adrenal_insufficiency': {'symptoms': {'fatigue': 0.90, 'muscle_weakness': 0.85, 'loss_appetite': 0.80, 'weight_loss': 0.80, 'abdominal_pain': 0.75}, 'bias': -3.5},
            'pituitary_disorders': {'symptoms': {'headache': 0.80, 'vision_problems': 0.85, 'fatigue': 0.80, 'mood_changes': 0.75, 'infertility': 0.70}, 'bias': -4.0},
            'glaucoma': {'symptoms': {'blind_spots': 0.90, 'tunnel_vision': 0.85, 'severe_headache': 0.80, 'eye_pain': 0.85, 'blurred_vision': 0.80}, 'bias': -3.0},
            'cataracts': {'symptoms': {'clouded_vision': 0.95, 'sensitivity_light': 0.85, 'difficulty_seeing_night': 0.90, 'fading_colors': 0.80, 'double_vision': 0.75}, 'bias': -2.5},
            'macular_degeneration': {'symptoms': {'partial_vision_loss': 0.95, 'straight_lines_appear_wavy': 0.90, 'blurred_vision': 0.85, 'difficulty_adapting_low_light': 0.80}, 'bias': -3.0},
            'hearing_loss': {'symptoms': {'muffling_speech': 0.90, 'difficulty_understanding_words': 0.85, 'trouble_hearing_consonants': 0.80, 'asking_others_speak_slowly': 0.75}, 'bias': -2.5},
            'tinnitus': {'symptoms': {'ringing_ears': 0.95, 'buzzing_ears': 0.90, 'roaring_ears': 0.85, 'clicking_ears': 0.80}, 'bias': -2.5},
            'sleep_apnea': {'symptoms': {'loud_snoring': 0.90, 'stop_breathing_sleep': 0.95, 'gasping_air_sleep': 0.90, 'morning_headache': 0.75, 'daytime_sleepiness': 0.85}, 'bias': -2.5},
            'insomnia': {'symptoms': {'difficulty_falling_asleep': 0.95, 'waking_up_night': 0.90, 'waking_up_early': 0.85, 'daytime_tiredness': 0.80}, 'bias': -2.0},
            'gerd': {'symptoms': {'heartburn': 0.95, 'chest_pain': 0.80, 'difficulty_swallowing': 0.85, 'regurgitation': 0.90, 'sensation_lump_throat': 0.75}, 'bias': -2.0},
            'ibs': {'symptoms': {'abdominal_pain': 0.85, 'bloating': 0.80, 'gas': 0.80, 'diarrhea': 0.75, 'constipation': 0.75}, 'bias': -2.0},
            'gallstones': {'symptoms': {'sudden_intense_pain_abdomen': 0.95, 'back_pain': 0.80, 'nausea': 0.75, 'vomiting': 0.75, 'digestive_problems': 0.70}, 'bias': -2.8},
            'kidney_stones': {'symptoms': {'severe_pain_side_back': 0.95, 'pain_urination': 0.90, 'pink_red_brown_urine': 0.85, 'nausea': 0.80, 'frequent_urination': 0.75}, 'bias': -2.8},
            'uti': {'symptoms': {'strong_urge_urinate': 0.90, 'burning_sensation_urination': 0.95, 'cloudy_urine': 0.85, 'red_pink_urine': 0.80, 'pelvic_pain': 0.75}, 'bias': -2.0},
            'benign_prostatic_hyperplasia': {'symptoms': {'frequent_urination': 0.90, 'trouble_starting_urination': 0.85, 'weak_urine_stream': 0.85, 'dribbling_urination': 0.80}, 'bias': -2.5},
            'endometriosis': {'symptoms': {'painful_periods': 0.95, 'pain_intercourse': 0.85, 'pain_bowel_movements': 0.80, 'excessive_bleeding': 0.75, 'infertility': 0.70}, 'bias': -3.0},
            'pcos': {'symptoms': {'irregular_periods': 0.95, 'excess_androgen': 0.90, 'polycystic_ovaries': 0.95, 'weight_gain': 0.80, 'acne': 0.75}, 'bias': -3.0},
            'preeclampsia': {'symptoms': {'high_blood_pressure': 0.95, 'severe_headaches': 0.90, 'changes_vision': 0.85, 'swelling_face_hands': 0.80}, 'bias': -3.5},
            'gestational_diabetes': {'symptoms': {'increased_thirst': 0.85, 'frequent_urination': 0.90, 'fatigue': 0.75, 'nausea': 0.70}, 'bias': -2.8},
            'myocardial_infarction': {'symptoms': {'chest_pain': 0.95, 'shortness_breath': 0.90, 'cold_sweat': 0.85, 'fatigue': 0.80, 'nausea': 0.75}, 'bias': -3.0},
            'atrial_fibrillation': {'symptoms': {'palpitations': 0.95, 'weakness': 0.85, 'fatigue': 0.85, 'lightheadedness': 0.80, 'shortness_breath': 0.75}, 'bias': -2.8},
            'heart_failure': {'symptoms': {'shortness_breath': 0.95, 'fatigue': 0.90, 'swollen_legs': 0.90, 'rapid_heartbeat': 0.85, 'persistent_cough': 0.80}, 'bias': -3.0},
            'peripheral_artery_disease': {'symptoms': {'leg_pain_walking': 0.90, 'leg_numbness': 0.85, 'cold_legs': 0.80, 'sores_toes': 0.75, 'shiny_skin_legs': 0.70}, 'bias': -3.0},
            'deep_vein_thrombosis': {'symptoms': {'swelling_leg': 0.95, 'pain_leg': 0.90, 'red_skin_leg': 0.85, 'warmth_leg': 0.85}, 'bias': -3.5},
            'pulmonary_embolism': {'symptoms': {'shortness_breath': 0.95, 'chest_pain': 0.90, 'cough': 0.80, 'faintness': 0.85, 'rapid_pulse': 0.85}, 'bias': -3.5},
            'sepsis': {'symptoms': {'fever': 0.90, 'low_body_temperature': 0.85, 'rapid_heart_rate': 0.90, 'rapid_breathing': 0.90, 'confusion': 0.85}, 'bias': -4.0},
            'meningitis': {'symptoms': {'high_fever': 0.90, 'stiff_neck': 0.95, 'severe_headache': 0.90, 'nausea': 0.80, 'confusion': 0.85, 'sensitivity_light': 0.80}, 'bias': -4.5},
            'encephalitis': {'symptoms': {'headache': 0.90, 'fever': 0.85, 'muscle_aches': 0.80, 'confusion': 0.90, 'seizures': 0.85}, 'bias': -4.5},
            'appendicitis': {'symptoms': {'pain_lower_right_abdomen': 0.99, 'nausea': 0.85, 'vomiting': 0.80, 'loss_appetite': 0.75, 'fever': 0.70}, 'bias': -3.0},
            'cholecystitis': {'symptoms': {'severe_pain_upper_right_abdomen': 0.95, 'pain_radiating_shoulder': 0.85, 'tenderness_abdomen': 0.90, 'nausea': 0.80}, 'bias': -3.0},
            'pancreatitis': {'symptoms': {'upper_abdominal_pain': 0.95, 'abdominal_pain_back': 0.90, 'tenderness_abdomen': 0.85, 'fever': 0.80, 'rapid_pulse': 0.80}, 'bias': -3.5},
            'gastritis': {'symptoms': {'gnawing_pain_abdomen': 0.90, 'nausea': 0.85, 'vomiting': 0.80, 'fullness_abdomen': 0.80}, 'bias': -2.5},
            'peptic_ulcer': {'symptoms': {'burning_stomach_pain': 0.95, 'feeling_full': 0.85, 'heartburn': 0.80, 'nausea': 0.75}, 'bias': -2.5},
            'diverticulitis': {'symptoms': {'pain_abdominal': 0.90, 'nausea': 0.80, 'fever': 0.75, 'constipation': 0.70}, 'bias': -2.8},
            'hemorrhoids': {'symptoms': {'itching_anal': 0.90, 'pain_anal': 0.85, 'swelling_anal': 0.80, 'bleeding_bowel_movements': 0.85}, 'bias': -2.0},
            'hernia': {'symptoms': {'bulge_abdomen': 0.95, 'pain_lift_heavy': 0.90, 'ache_bulge': 0.85, 'nausea': 0.70}, 'bias': -2.5},
            'fracture': {'symptoms': {'pain': 0.95, 'swelling': 0.90, 'bruising': 0.85, 'deformity': 0.95, 'inability_move': 0.90}, 'bias': -2.0},
            'spinal_stenosis': {'symptoms': {'numbness_extremities': 0.85, 'weakness_extremities': 0.80, 'neck_pain': 0.75, 'balance_problems': 0.70}, 'bias': -3.0},
            'herniated_disc': {'symptoms': {'arm_leg_pain': 0.90, 'numbness': 0.85, 'weakness': 0.80}, 'bias': -2.5},
            'scoliosis': {'symptoms': {'uneven_shoulders': 0.95, 'uneven_waist': 0.90, 'one_hip_higher': 0.90}, 'bias': -2.5},
            'tendonitis': {'symptoms': {'pain_tendon': 0.95, 'tenderness': 0.90, 'mild_swelling': 0.80}, 'bias': -2.0},
            'bursitis': {'symptoms': {'aching_pain': 0.90, 'stiffness': 0.85, 'swollen_joint': 0.80, 'redness': 0.75}, 'bias': -2.0},
            'carpal_tunnel_syndrome': {'symptoms': {'numbness_fingers': 0.95, 'weakness_hand': 0.85, 'tingling_fingers': 0.90}, 'bias': -2.2},
            'plantar_fasciitis': {'symptoms': {'stabbing_pain_heel': 0.95, 'pain_morning': 0.90, 'pain_after_exercise': 0.80}, 'bias': -2.0},
            'shingles': {'symptoms': {'pain_burning': 0.95, 'red_rash': 0.90, 'fluid_filled_blisters': 0.90, 'itching': 0.85}, 'bias': -2.8},
            'herpes_simplex': {'symptoms': {'tingling_itching': 0.90, 'sores': 0.95, 'fever': 0.70, 'swollen_lymph_nodes': 0.75}, 'bias': -2.5},
            'chickenpox': {'symptoms': {'itchy_rash': 0.99, 'fever': 0.85, 'fatigue': 0.80, 'loss_appetite': 0.75}, 'bias': -2.0},
            'measles': {'symptoms': {'fever': 0.95, 'dry_cough': 0.85, 'runny_nose': 0.80, 'sore_throat': 0.75, 'inflamed_eyes': 0.80, 'koplik_spots': 0.95, 'skin_rash': 0.95}, 'bias': -3.0},
            'mumps': {'symptoms': {'swollen_salivary_glands': 0.99, 'fever': 0.85, 'headache': 0.80, 'muscle_aches': 0.80, 'weakness': 0.75}, 'bias': -3.0},
            'rubella': {'symptoms': {'mild_fever': 0.80, 'headache': 0.70, 'runny_nose': 0.70, 'inflamed_eyes': 0.70, 'pink_rash': 0.95, 'swollen_lymph_nodes': 0.85}, 'bias': -2.5},
            'whooping_cough': {'symptoms': {'runny_nose': 0.80, 'nasal_congestion': 0.80, 'red_watery_eyes': 0.75, 'severe_cough': 0.95}, 'bias': -2.8},
            'diptheria': {'symptoms': {'thick_gray_coating_throat': 0.99, 'sore_throat': 0.90, 'swollen_glands': 0.85, 'difficulty_breathing': 0.90}, 'bias': -3.5},
            'tetanus': {'symptoms': {'jaw_cramping': 0.95, 'muscle_spasms': 0.90, 'painful_muscle_stiffness': 0.90, 'trouble_swallowing': 0.85}, 'bias': -4.0},
            'polio': {'symptoms': {'fever': 0.80, 'sore_throat': 0.75, 'headache': 0.80, 'vomiting': 0.75, 'fatigue': 0.80, 'muscle_weakness': 0.90, 'meningitis': 0.85}, 'bias': -4.5},
        }
        
        # Helper to auto-generate display names map from the keys above
        self.symptom_display_names = self._generate_symptom_names()

    def _generate_symptom_names(self):
        """Auto-generate display names from symptom keys"""
        names = {}
        for disease, data in self.disease_weights.items():
            for symptom_key in data['symptoms'].keys():
                names[symptom_key] = symptom_key.replace('_', ' ').title()
        return names

    @staticmethod
    def sigmoid(z: float) -> float:
        """Sigmoid activation function for logistic regression"""
        return 1 / (1 + np.exp(-z))
    
    # NOTE:
    # Raw sigmoid probabilities tend to be overconfident.
    # Temperature scaling is applied to improve calibration and interpretability.

    def calibrated_sigmoid(self, z: float, temperature: float = 1.8) -> float:
        """
        Temperature-scaled sigmoid for probability calibration.
        Higher temperature -> less overconfident probabilities.
        """
        return 1 / (1 + np.exp(-(z / temperature)))

    def _calculate_bmi(self, height_cm: float, weight_kg: float) -> float:
        if not height_cm or not weight_kg:
            return None
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    def _global_bmi_effect(self, bmi: float) -> float:
        """
        Global BMI impact on disease risk (applies to all diseases).
        Small values so symptoms remain dominant.
        """
        if bmi is None:
            return 0.0

        if bmi < 18.5:
            return 0.25   # underweight risk
        elif bmi < 25:
            return 0.0    # normal
        elif bmi < 30:
            return 0.35   # overweight
        else:
            return 0.6    # obese

    # Normalize disease key
    def _get_disease_key(self, disease_name: str) -> str:
        """
        Normalize and fuzzy match disease name to internal key.
        """
        disease_key = disease_name.lower().replace(' ', '_').replace('-', '_')
        
        # Exact match check
        if disease_key in self.disease_weights:
            return disease_key
            
        # Fuzzy match: try to find a key that matches when underscores are removed
        normalized_input = disease_key.replace('_', '')
        for key in self.disease_weights.keys():
            if key.replace('_', '') == normalized_input:
                return key
                
        # If no match found, raise ValueError
        raise ValueError(f"Disease '{disease_name}' (key: {disease_key}) not found in model")

    def predict_disease_probability(self, disease: str, symptoms: List[str], age: int = None, height_cm: float = None, weight_kg: float = None) -> Dict:
        """
        Predict disease probability based on selected symptoms and optional age.
        """
        # Use helper for robust lookup
        disease_key = self._get_disease_key(disease)
        
        weights = self.disease_weights[disease_key]
        symptom_weights = weights['symptoms']
        bias = weights['bias']

        # Adjust bias based on age
        if age is not None:
            if age > 50:
                bias += 0.5  # Higher risk for older age
            elif age < 20:
                bias -= 0.5  # Lower risk for younger age
        z  = bias 

        # BMI contribution
        bmi = self._calculate_bmi(height_cm, weight_kg)
        bmi_effect = self._global_bmi_effect(bmi)
        z += bmi_effect

        bmi_category = None
        if bmi:
            if bmi < 18.5:
                bmi_category = "Underweight"
            elif bmi < 25:
                bmi_category = "Normal"
            elif bmi < 30:
                bmi_category = "Overweight"
            else:
                bmi_category = "Obese"
        
        matched_symptoms = []
        
        for symptom in symptoms:
            if symptom in symptom_weights:
                z += symptom_weights[symptom]
                matched_symptoms.append(symptom)
        
        raw_probability = self.sigmoid(z)
        calibrated_probability = self.calibrated_sigmoid(z)
        
        prior = min(0.95, max(0.05, raw_probability))
        likelihood = 0.75 + (raw_probability * 0.20)
        
        return {
            'disease': disease,
            'raw_probability': float(raw_probability),
            'calibrated_probability': float(calibrated_probability),
            'prior_probability': float(prior),
            'likelihood': float(likelihood),
            'symptoms_matched': len(matched_symptoms),
            'total_symptoms': len(symptoms),
            'confidence_score': self._calculate_confidence(len(matched_symptoms), raw_probability, bmi),
            'bmi': round(bmi, 2) if bmi else None,
            'bmi_category': bmi_category,
            'bmi_effect': bmi_effect
        }
    
    def _calculate_confidence(self, num_symptoms: int, probability: float, bmi : float = None) -> float:
        symptom_factor = min(1.0, num_symptoms / 5)
        bmi_factor = 0.1 if bmi and (bmi < 18.5 or bmi > 30) else 0.0
        confidence = (symptom_factor * 0.5) + (probability * 0.4) + bmi_factor
        return float(confidence)
    
    def get_available_diseases(self) -> List[str]:
        return list(self.disease_weights.keys())
    
    def get_disease_symptoms(self, disease: str) -> Dict[str, str]:
        disease_key = self._get_disease_key(disease)
        
        symptom_keys = self.disease_weights[disease_key]['symptoms'].keys()
        return {
            key: self.symptom_display_names.get(key, key.replace('_', ' ').title())
            for key in symptom_keys
        }
    
    def predict_multiple_diseases(self, symptoms: List[str]) -> List[Dict]:
        predictions = []
        for disease in self.disease_weights.keys():
            try:
                prediction = self.predict_disease_probability(disease, symptoms)
                predictions.append(prediction)
            except Exception:
                logger.error(
                    f"Prediction failed for disease '{disease}'",
                    exc_info=True
                )

        # Sort by raw probability (highest first)
        predictions.sort(key=lambda x: x['calibrated_probability'], reverse=True)
        return predictions

    
    def get_symptom_importance(self, disease: str) -> Dict[str, float]:
        disease_key = self._get_disease_key(disease)
        
        symptoms = self.disease_weights[disease_key]['symptoms']
        importance = {
            self.symptom_display_names.get(key, key): weight
            for key, weight in symptoms.items()
        }
        return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))

    def analyze_missing_symptoms(self, disease: str, present_symptoms: List[str]) -> List[Dict[str, float]]:
        """
        Identify high-importance symptoms for a disease that are missing from the present symptoms.
        
        Args:
            disease: The name of the disease to analyze.
            present_symptoms: List of symptom keys provided by the user.
            
        Returns:
            List of missing symptoms with their weights, sorted by importance.
        """
        try:
            disease_key = self._get_disease_key(disease)
        except ValueError:
            return []

        # Get all symptoms and weights for the disease
        all_symptoms = self.disease_weights[disease_key]['symptoms']
        
        missing = []
        for symptom_key, weight in all_symptoms.items():
            # If the symptom is NOT in the user's list AND has high importance
            if symptom_key not in present_symptoms and weight >= 0.75:
                missing.append({
                    'key': symptom_key,
                    'name': self.symptom_display_names.get(symptom_key, symptom_key.replace('_', ' ').title()),
                    'weight': weight
                })
        
        # Sort by weight descending
        missing.sort(key=lambda x: x['weight'], reverse=True)
        
        # Return top 5 missing symptoms
        return missing[:5]

ml_model = DiseaseMLModel()