import sys
from flask import Flask, request, abort, jsonify
from flask_cors import CORS
from models import setup_db, Question, Category
import random


QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    return questions[start:end]


def dump_categories(categories):
    result = {}
    for item in categories:
        result[item.id] = item.type
    return result


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.after_request
    def after_request(response):
        response.headers.add(
            'Access-Control-Allow-Headers', 'Content-Type, Authorization, true'
        )
        response.headers.add(
            'Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS'
        )

        return response

    @app.route('/api/v1.0/categories')
    def get_categories():
        categories = Category.query.all()

        if (len(categories) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'categories': dump_categories(categories)
        })

    @app.route('/api/v1.0/questions')
    def get_questions():
        questions = Question.query.all()
        categories = Category.query.all()

        selected_questions = paginate_questions(request, questions)

        if (len(selected_questions) == 0):
            abort(404)

        return jsonify({
            'success': True,
            'questions': selected_questions,
            'total_questions': len(questions),
            'categories': dump_categories(categories)
        })

    @app.route('/api/v1.0/questions/<int:id>', methods=['DELETE'])
    def delete_questions(id):
        question = Question.query.filter(Question.id == id).one_or_none()

        if question is None:
            abort(422)

        try:
            Question.delete(question)
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
        except:
            print(sys.exc_info())
            abort(422)
        finally:
            return jsonify({
                'success': True,
                'deleted': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })

    @app.route('/api/v1.0/questions', methods=['POST'])
    def create_question():
        body = request.get_json()
        new_question = body['question']
        new_answer = body['answer']
        new_difficulty = body['difficulty']
        new_category = body['category']

        try:
            question = Question(
                new_question, 
                new_answer,
                new_category, 
                new_difficulty
            )
            
            question.insert()
            current_questions = paginate_questions(request, Question.query.all())
            
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(current_questions)
            })
            
        except:
            print(sys.exc_info())
            abort(422)

    @app.route('/api/v1.0/questions/search', methods=['POST'])
    def search_questions():
        search_term = request.get_json()['searchTerm']
        search_result = Question.query.filter(
            Question.question.ilike(f'%{search_term}%')).all()

        if not search_result:
            abort(404)
            
        return jsonify(
            {
                'success': True,
                'questions': [question.format() for question in search_result],
                'totalQuestions': len(search_result),
                'currentCategory': search_result[0].category,
            })

    @app.route('/api/v1.0/categories/<int:id>/questions')
    def get_questions_by_category_id(id):
        questions = Question.query.filter(Question.category == id).all()
        
        if not questions:
            abort(404)
        
        return jsonify({
          'questions': [question.format() for question in questions],
          'totalQuestions': len(questions),
          'success': True
        })
    
    @app.route('/api/v1.0/quizzes', methods=['POST'])
    def get_quizzes():
        body = request.get_json()
        previous_questions = body['previous_questions']
        quiz_category = body['quiz_category']
        questions = []
                  
        if quiz_category['id'] != 0:
            questions = Question.query.filter(Question.category == quiz_category['id']).all()
        else:
            questions = Question.query.all()
        
        if not questions:
            abort(404)
        
        if previous_questions:
            questions = list(filter(lambda item: item.id not in previous_questions, questions))

        try:   
            return jsonify({
                'success': True,
                'question': random.choice([q.format() for q in questions]),
            })
        except:
            print(sys.exc_info)
            abort(422)
    
    @app.errorhandler(404)
    def not_found(error):
        return (
            jsonify({"success": False, "error": 404, "message": "resource not found"}),
            404,
        )

    @app.errorhandler(422)
    def unprocessable(error):
        return (
            jsonify({"success": False, "error": 422, "message": "unprocessable"}),
            422,
        )
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({"success": False, "error": 400, "message": "bad request"}), 400
    
    return app
