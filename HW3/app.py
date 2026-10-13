from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)

# SQLite 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///todo.db'

db = SQLAlchemy(app)


# Todo 테이블
class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(100), nullable=False)
    note = db.Column(db.String(200))
    done = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Todo {self.id} {self.text}>'


# 목록 조회 + 새 할 일 추가
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        todo = Todo(
            text=request.form['todo'],
            note=request.form['note']
        )

        db.session.add(todo)
        db.session.commit()

        return redirect(url_for('index'))

    todos = Todo.query.all()

    return render_template(
        'index.html',
        todos=todos
    )


# 완료 / 완료 해제
@app.route('/toggle/<int:id>')
def toggle(id):
    todo = db.get_or_404(Todo, id)

    todo.done = not todo.done

    db.session.commit()

    return redirect(url_for('index'))


# 할 일 수정
@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    todo = db.get_or_404(Todo, id)

    if request.method == 'POST':
        todo.text = request.form['todo']
        todo.note = request.form['note']

        db.session.commit()

        return redirect(url_for('index'))

    return render_template(
        'edit.html',
        todo=todo
    )


# 할 일 삭제
@app.route('/delete/<int:id>')
def delete(id):
    todo = db.get_or_404(Todo, id)

    db.session.delete(todo)
    db.session.commit()

    return redirect(url_for('index'))


# 데이터베이스 테이블 생성
with app.app_context():
    db.create_all()


if __name__ == '__main__':
    app.run(debug=True)