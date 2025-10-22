from flask import Blueprint, render_template

scalability_bp = Blueprint("scalability", __name__)

@scalability_bp.route("/scalability")
def scalability():
    return render_template("Scalability.html")
