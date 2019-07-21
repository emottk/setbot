import os

from app import app, db
from app.models import User, Score
from flask import abort, Flask, jsonify, request
from datetime import datetime


def is_request_valid(request):
	is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
	is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

	return is_token_valid and is_team_id_valid


@app.route('/set_score', methods=['POST'])
def set_score():
	if not is_request_valid(request):
		abort(400)
	
	user_id = request.form["user_id"]
	user_name = request.form["user_name"]
	text_input = request.form["text"]
	if text_input:
		params = text_input.split()
	else:
		return jsonify(
			response_type='in_channel',
			type='section',
			text="I didn't catch that! Type 'help' for a list of appropriate commands"
			)
	if params[0] == "help":
		return jsonify(
			response_type='in_channel',
			text="Here are some commands you can try:\n *score* [set score format including backticks and hours]\n *past_scores*\n *compare_scores* [slack username]"
			)

	if not User.query.filter_by(slack_userid=user_id).first():
		user = User(slack_userid=user_id, slack_username=user_name)
		db.session.add(user)
		db.session.commit()

	else:
		user = User.query.filter_by(slack_userid=user_id).first()
	
	if params[0] == "score":
		print(params)
		try:
			value = datetime.strptime(params[1], "`%H hours %M minutes and %S.%f seconds`").time()
			print(f'hitting try with {value} as the value')
		except Exception as e:
			print(f'Hitting except with {e} as the error')
			return jsonify(
				response_type='in_channel',
				text="*Uh oh*, I didn't catch that! Please input your score in a code block using backticks, in set score form ex: `0 hours 00 minutes and 0.00 seconds`"
				)
 
		score = Score(orig_input=params[1], user=user, value=value)
		db.session.add(score)
		db.session.commit()

		return jsonify(
			response_type='in_channel',
			text=f'Your time {params[1]} has been saved! Good job today!',
		)

	return jsonify(
		response_type='in_channel',
		text="Looks like you didn't type a valid command. Try `help` for a list of possible commands!"
		)

@app.route('/past_scores', methods=['POST'])
def past_scores():
	if not is_request_valid(request):
        	abort(400)

	user_id = request.form["user_id"]
	return_text = ''
	user = User.query.filter_by(slack_userid=user_id).first()

	try:
		scores = user.set_scores.all()
	except:
		return jsonify(
			response_type='in_channel',
			text="You don't have any scores yet! Add one by using `*/set_score*`!"
		)

	for val in scores:
		return_text += f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n'
	
	print(f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n')

	return jsonify(
		response_type='in_channel',
		text=f'Here are your past scores!\n{return_text}',
	)
