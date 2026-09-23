from flask import Flask, render_template

app = Flask(__name__)


# 메인 페이지 : 이름과 학번
@app.route("/")
def home():
    return render_template(
        "index.html",
        name="이상윤",
        student_id="23013335"
    )

if __name__ == "__main__":
    app.run(debug=True)