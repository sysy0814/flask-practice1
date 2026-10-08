from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# 간단한 in-memory 데이터 저장소
todos = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        todo = request.form['todo']
        todos.append({
            'text': todo,
            'done': False
        })
        return redirect(url_for('index'))
    return render_template('index.html', todos=todos)

@app.route('/toggle/<int:index>')
def toggle(index):
    if 0 <= index < len(todos):
        todos[index]['done'] = not todos[index]['done']

    return redirect(url_for('index'))

@app.route('/delete/<int:index>')
def delete(index):
    if 0 <= index < len(todos):
        del todos[index]
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)