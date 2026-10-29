
import os

from flask import Flask, Blueprint, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_restx import Api, Resource, fields


app = Flask(__name__)

# 데이터베이스 설정
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "TODO_DATABASE_URI", "sqlite:///todo.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["ERROR_404_HELP"] = False
app.config["RESTX_JSON"] = {"ensure_ascii": False}

db = SQLAlchemy(app)


# Todo 모델
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(500), default="")
    done = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"<Todo {self.id} {self.text}>"


# ==================================================
# 기존 웹 화면
# ==================================================

# 할 일 목록 조회 및 추가
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        todo = Todo(
            text=request.form["todo"],
            note=request.form.get("note", "")
        )

        db.session.add(todo)
        db.session.commit()

        return redirect(url_for("index"))

    todos = Todo.query.all()
    return render_template("index.html", todos=todos)


# 완료 상태 변경
@app.route("/toggle/<int:id>")
def toggle(id):
    todo = db.get_or_404(Todo, id)

    todo.done = not todo.done
    db.session.commit()

    return redirect(url_for("index"))


# 할 일 수정 - HW3 기능 유지
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    todo = db.get_or_404(Todo, id)

    if request.method == "POST":
        todo.text = request.form["todo"]
        todo.note = request.form.get("note", "")

        db.session.commit()

        return redirect(url_for("index"))

    return render_template("edit.html", todo=todo)


# 할 일 삭제
@app.route("/delete/<int:id>")
def delete(id):
    todo = db.get_or_404(Todo, id)

    db.session.delete(todo)
    db.session.commit()

    return redirect(url_for("index"))


# ==================================================
# RESTful API
# ==================================================

# API Blueprint
api_bp = Blueprint("api", __name__, url_prefix="/api")

api = Api(
    api_bp,
    version="1.0",
    title="Todo API",
    description="Todo 앱의 RESTful API",
    doc="/docs"
)

ns = api.namespace(
    "todos",
    description="할 일 목록을 관리하는 API"
)


# API 응답 모델
todo_model = api.model("Todo", {
    "id": fields.Integer(
        readonly=True,
        description="할 일 번호"
    ),
    "text": fields.String(
        required=True,
        description="할 일 글자",
        example="우유 사기"
    ),
    "done": fields.Boolean(
        description="완료 여부",
        example=False
    ),
    "note": fields.String(
        description="설명",
        example="2리터짜리로"
    )
})


# API 입력 모델
todo_input = api.model("TodoInput", {
    "text": fields.String(
        required=True,
        description="할 일 글자",
        example="우유 사기"
    ),
    "done": fields.Boolean(
        description="완료 여부",
        example=False
    ),
    "note": fields.String(
        description="설명",
        example="2리터짜리로"
    )
})


# 전체 목록 조회 및 새 할 일 추가
@ns.route("/")
class TodoList(Resource):

    @ns.doc("목록 보기")
    @ns.param(
        "done",
        "true 면 완료만, false 면 아직 안 한 것만"
    )
    @ns.marshal_list_with(todo_model)
    def get(self):
        """할 일을 돌려준다. done을 주면 걸러서 돌려준다"""

        q = Todo.query
        done = request.args.get("done")

        if done is not None:
            q = q.filter_by(done=(done.lower() == "true"))

        return q.all()

    @ns.doc("새로 만들기")
    @ns.expect(todo_input, validate=True)
    @ns.marshal_with(todo_model, code=201)
    def post(self):
        """할 일을 하나 만든다"""

        todo = Todo(
            text=api.payload["text"],
            done=api.payload.get("done", False),
            note=api.payload.get("note", "")
        )

        db.session.add(todo)
        db.session.commit()

        return todo, 201, {
            "Location": f"/api/todos/{todo.id}"
        }


# 할 일 한 건 조회, 수정, 삭제
@ns.route("/<int:id>")
@ns.param("id", "할 일의 줄 번호")
@ns.response(404, "그 번호의 할 일이 없습니다")
class TodoItem(Resource):

    @ns.doc("하나 보기")
    @ns.marshal_with(todo_model)
    def get(self, id):
        """할 일 하나를 돌려준다"""

        return get_or_abort(id)

    @ns.doc("통째로 바꾸기")
    @ns.expect(todo_input, validate=True)
    @ns.marshal_with(todo_model)
    def put(self, id):
        """할 일을 통째로 바꾼다"""

        todo = get_or_abort(id)

        todo.text = api.payload["text"]
        todo.done = api.payload.get("done", False)
        todo.note = api.payload.get("note", "")

        db.session.commit()

        return todo

    @ns.doc("일부만 바꾸기")
    @ns.expect(todo_input)
    @ns.marshal_with(todo_model)
    def patch(self, id):
        """보낸 칸만 수정한다"""

        todo = get_or_abort(id)

        if "text" in api.payload:
            todo.text = api.payload["text"]

        if "done" in api.payload:
            todo.done = api.payload["done"]

        if "note" in api.payload:
            todo.note = api.payload["note"]

        db.session.commit()

        return todo

    @ns.doc("지우기")
    @ns.response(
        204,
        "지웠습니다. 돌려줄 내용이 없습니다"
    )
    def delete(self, id):
        """할 일 하나를 지운다"""

        todo = get_or_abort(id)

        db.session.delete(todo)
        db.session.commit()

        return "", 204


# 없는 할 일에 대해 JSON 404 반환
def get_or_abort(id):
    todo = db.session.get(Todo, id)

    if todo is None:
        ns.abort(404, f"{id} 번 할 일이 없습니다")

    return todo


# API Blueprint 등록
app.register_blueprint(api_bp)


# 데이터베이스 테이블 자동 생성
with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
