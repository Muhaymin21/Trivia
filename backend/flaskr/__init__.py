import random

from flask import Flask, request, jsonify, abort
from flask_cors import CORS
from sqlalchemy import func

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 5


def paginate(page, selection):
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE
    questions = [question.format_output() for question in selection]
    current_questions = questions[start:end]
    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    '''
  @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
  '''
    CORS(app, resources={r"/*": {"origins": "*"}})

    # CORS()

    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response

    @app.route('/categories')
    def get_all_categories():
        categories = {}
        for categorie in Category.query.order_by(Category.id).all():
            categories[categorie.id] = categorie.type
        return jsonify({
            'success': True,
            'categories': categories,
        })

    @app.route('/questions')
    def get_all_questions_and_categories():
        selection = Question.query.order_by(Question.id).all()
        questions = paginate(request.args.get('page', 1, type=int), selection)
        categories = {}
        for categorie in Category.query.order_by(Category.id).all():
            categories[categorie.id] = categorie.type
        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(selection),
            'categories': categories,
        })

    @app.route('/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        question = Question.query.filter_by(id=question_id).one_or_none()
        if question is not None:
            try:
                question.delete()
                return jsonify({
                    'success': True
                })
            except:
                abort(422)
        else:
            abort(404)

    @app.route('/questions', methods=["POST"])
    def add_question():
        body = request.get_json()

        question = body.get('question')
        answer = body.get('answer')
        difficulty = body.get('difficulty')
        category = body.get('category')

        if question is None or answer is None or difficulty is None or category is None:
            abort(400)
        try:
            new_question = Question(question, answer, category, difficulty)
            new_question.insert()
            return jsonify({
                'success': True,
                'id': new_question.id
            }), 201
        except:
            abort(422)

    @app.route('/questions/search', methods=['POST'])
    def search():
        search_term = request.get_json().get('searchTerm', '')
        questions = []
        search_term = search_term.strip()
        if len(search_term) > 0:
            try:
                [
                    questions.append(search_question.format_output())
                    for search_question in
                    Question.query.filter(func.lower(Question.question).contains(search_term.lower())).all()
                ]
            except:
                abort(422)
        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(questions)
        })

    @app.route('/categories/<int:category_id>/questions')
    def get_categorie_questions(category_id):
        try:
            selection = Question.query.filter_by(category=category_id).order_by(Question.id).all()
            questions = paginate(request.args.get('page', 1, type=int), selection)
            return jsonify({
                'success': True,
                'questions': questions,
                'total_questions': len(selection),
                'current_category': category_id,
            })
        except:
            abort(422)

    @app.route('/quizzes', methods=['POST'])
    def quiz_next_question():
        body = request.get_json()

        previous_questions = body.get('previous_questions')
        quiz_category = body.get('quiz_category')

        if previous_questions is None or quiz_category is None:
            abort(400)
        quiz_category = quiz_category['id']
        try:
            if quiz_category == 0:
                questions = Question.query.order_by(func.random()).all()
            else:
                questions = Question.query.filter_by(category=quiz_category).all()
            max_question = len(questions)
            if max_question <= len(previous_questions):
                return jsonify({
                    'success': True,
                    'question': False,
                    'message': 'Maximum reached'
                })
            rand = random.randrange(0, max_question)
            new_question = questions[rand]
            while True:
                if new_question.id not in previous_questions:
                    break
                else:
                    rand = random.randrange(0, max_question)
                    new_question = questions[rand]
            return jsonify({
                'success': True,
                'question': {
                    'id': new_question.id,
                    'question': new_question.question,
                    'answer': new_question.answer
                }
            })
        except:
            abort(422)

    @app.errorhandler(404)
    def not_found(error):
        print(error)
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'Not found'
        }), 404

    @app.errorhandler(405)
    def not_found(error):
        print(error)
        return jsonify({
            "success": False,
            "error": 405,
            "message": "Method not allowed"
        }), 405

    @app.errorhandler(422)
    def not_found(error):
        print(error)
        return jsonify({
            "success": False,
            "error": 422,
            "message": "The server failed to process the request"
        }), 422

    @app.errorhandler(400)
    def not_found(error):
        print(error)
        return jsonify({
            "success": False,
            "error": 400,
            "message": "Bad request: Required data is missing"
        }), 400

    return app
