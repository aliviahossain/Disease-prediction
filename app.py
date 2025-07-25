from flask import Flask, request, jsonify, render_template
import csv

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/preset", methods=["POST"])
def preset():
    disease_name = request.json.get("disease")
    try:
        with open('hospital_data.csv', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                if row['Disease'].lower() == disease_name.lower():
                    p_d = float(row['Prevalence'])
                    sensitivity = float(row['Sensitivity'])
                    false_pos = float(row['FalsePositive'])

                    # Bayes' Theorem calculation
                    p_pos = (sensitivity * p_d) + (false_pos * (1 - p_d))
                    p_d_given_pos = (sensitivity * p_d) / p_pos

                    return jsonify({
                        "p_d_given_pos": round(p_d_given_pos, 4)
                    })
        return jsonify({"error": "Disease not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/disease", methods=["POST"])
def disease():
    data = request.json
    try:
        p_d = float(data.get("pD"))
        sensitivity = float(data.get("sensitivity"))
        false_pos = float(data.get("falsePositive"))

        # Bayes' Theorem calculation
        p_pos = (sensitivity * p_d) + (false_pos * (1 - p_d))
        p_d_given_pos = (sensitivity * p_d) / p_pos

        return jsonify({
            "p_d_given_pos": round(p_d_given_pos, 4)
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == "__main__":
    app.run(debug=True)


