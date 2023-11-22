from flask import Flask, request, jsonify
from flask.views import MethodView
from flask_sqlalchemy import SQLAlchemy
from flask_basicauth import BasicAuth
from wtforms import Form, StringField, BooleanField, validators
from wtforms.validators import Length
from werkzeug.datastructures import MultiDict


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:12345@localhost:3306/task_management'
db = SQLAlchemy(app)


# Basic Authentication
app.config['BASIC_AUTH_USERNAME'] = 'task'
app.config['BASIC_AUTH_PASSWORD'] = '123'
basic_auth = BasicAuth(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key = True)
    title = db.Column(db.String(50), nullable = False)
    description = db.Column(db.Text)
    done = db.Column(db.Boolean, default = False)

    def serialize(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'done': self.done
        }


class TaskForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=50)])
    description = StringField('Description')
    done = BooleanField('Done')


class TaskAPI(MethodView):
    @basic_auth.required
    def get(self, task_id=None):
        try:
            if task_id is None:
                tasks = Task.query.all()
                return jsonify(tasks=[task.serialize() for task in tasks])
            else:
                task = Task.query.get(task_id)
                if task:
                    return jsonify(task.serialize())
                else:
                    return jsonify(error="Task not found"), 404

        except Exception as e:
            return jsonify(error = str(e)), 400


    @basic_auth.required
    def post(self):
        try:
            # Convert JSON data to MultiDict
            form_data = MultiDict(request.json)

            # Validate JSON data using TaskForm
            form = TaskForm(form_data)
            if form.validate():
                # Access validated data
                title = form.data['title']
                description = form.data['description']
                done = form.data['done']

                # Use the validated data as needed
                new_task = Task(
                    title = title,
                    description = description,
                    done = done
                )

                db.session.add(new_task)
                db.session.commit()

                return jsonify(new_task.serialize()), 201
            else:
                return jsonify(error=form.errors), 400

        except Exception as e:
            return jsonify(error=str(e)), 400


    @basic_auth.required
    def put(self, task_id):
        try:
            # Get the existing task
            task = Task.query.get(task_id)
            if not task:
                return jsonify(error="Task not found"), 404

            # Convert JSON data to MultiDict
            form_data = MultiDict(request.json)

            # Validate JSON data using TaskForm
            form = TaskForm(form_data)
            if form.validate():
                # Access validated data
                task.title = form.data['title']
                task.description = form.data['description']
                task.done = form.data['done']

                db.session.commit()

                return jsonify(task.serialize())
            else:
                return jsonify(error = form.errors), 400

        except Exception as e:
            return jsonify(error=str(e)), 400


    @basic_auth.required
    def delete(self, task_id):
        try:
            # Get the existing task
            task = Task.query.get(task_id)
            if not task:
                return jsonify(error="Task not found"), 404

            db.session.delete(task)
            db.session.commit()

            return jsonify(message="Task deleted successfully")

        except Exception as e:
            return jsonify(error = str(e)), 400


# Add URLs and Views
app.add_url_rule('/tasks/', view_func=TaskAPI.as_view('tasks_api'), methods = ['GET', 'POST'])
app.add_url_rule('/tasks/<int:task_id>/', view_func = TaskAPI.as_view('task_api'), methods=['GET', 'PUT', 'DELETE'])

# Create tables if they do not exist
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True)