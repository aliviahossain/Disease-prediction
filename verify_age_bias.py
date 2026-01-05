from backend.models.ml_model import ml_model

def test_age_bias():
    disease = 'diabetes'
    symptoms = ['increased_thirst', 'frequent_urination']
    
    # Test without age (baseline)
    print(f"Testing {disease} with symptoms: {symptoms}")
    res_baseline = ml_model.predict_disease_probability(disease, symptoms)
    prob_baseline = res_baseline['raw_probability']
    print(f"Baseline Probability (No Age): {prob_baseline:.4f}")
    
    # Test with Age > 50 (Higher Risk)
    age_old = 60
    res_old = ml_model.predict_disease_probability(disease, symptoms, age=age_old)
    prob_old = res_old['raw_probability']
    print(f"Probability (Age {age_old}): {prob_old:.4f}")
    
    # Test with Age < 20 (Lower Risk)
    age_young = 15
    res_young = ml_model.predict_disease_probability(disease, symptoms, age=age_young)
    prob_young = res_young['raw_probability']
    print(f"Probability (Age {age_young}): {prob_young:.4f}")
    
    # Verification
    if prob_old > prob_baseline:
        print("✅ SUCCESS: Age > 50 increased probability.")
    else:
        print("❌ FAIL: Age > 50 did NOT increase probability.")
        
    if prob_young < prob_baseline:
        print("✅ SUCCESS: Age < 20 decreased probability.")
    else:
        print("❌ FAIL: Age < 20 did NOT decrease probability.")

if __name__ == "__main__":
    test_age_bias()
