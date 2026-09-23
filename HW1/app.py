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

# 프로필 페이지 : 취미 3개
@app.route("/profile")
def profile():
    hobbies = ["게임", "코딩", "음악 감상"]

    return render_template(
        "profile.html",
        hobbies=hobbies
    )

if __name__ == "__main__":
    app.run(debug=True)