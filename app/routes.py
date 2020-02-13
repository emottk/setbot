import os

from app import app, db
from app.models import User, Score
from flask import abort, Flask, jsonify, request
from datetime import datetime
import random


def is_request_valid(request):
	is_token_valid = request.form['token'] == os.environ['SLACK_VERIFICATION_TOKEN']
	is_team_id_valid = request.form['team_id'] == os.environ['SLACK_TEAM_ID']

	return is_token_valid and is_team_id_valid

#def check_score_input(score):
	#try:
		#value = datetime.strptime(score, "%H hours %M minutes and %S.%f s\
#econds`").time()
#	except Exception as e:

@app.route('/set', methods=['POST'])
def set_score():
	if not is_request_valid(request):
		abort(400)

	commands = ["help", "score", "past_scores", "compare_scores", "today", "my_best"]
	user_id = request.form["user_id"]
	user_name = request.form["user_name"]
	text_input = request.form["text"]
	
	if text_input:
		params = text_input.split()
	else:
		return jsonify(
			response_type='ephermal',
			type='section',
			text="I didn't catch that! Type 'help' for a list of appropriate commands"
			)

	if params[0] not in commands:
		return jsonify(
                        response_type='ephemeral',
                        type='section',
                        text="I didn't catch that! Type 'help' for a list of appropriate commands"
                        )

	if params[0] == "help":
		return jsonify(
			response_type='ephemeral',
			text="Here are some commands you can try:\n *score* [set score format including backticks and hours]\n *past_scores*\n *compare_scores* [slack username]\n *today*"
			)

	if not User.query.filter_by(slack_userid=user_id).first():
		user = User(slack_userid=user_id, slack_username=user_name)
		db.session.add(user)
		db.session.commit()

	else:
		user = User.query.filter_by(slack_userid=user_id).first()
	
	if params[0] == "score":
		input_value = text_input.split(" `")
		try:
			value = datetime.strptime(input_value[1], "%H hours %M minutes and %S.%f seconds`").time()
		except Exception as e:
			return jsonify(
				response_type='ephemeral',
				text="*Uh oh*, I didn't catch that! Please input your score in a code block using backticks, in set score form ex: `0 hours 00 minutes and 0.00 seconds`"
				)
		score = Score(orig_input=f'`{input_value[1]}', user=user, value=value)
		db.session.add(score)
		db.session.commit()
		congrats = ["Good job!", "Well done!", "Very impressive.", "Something something blind dog sunshine something."]
		return jsonify(
			response_type='in_channel',
			text=f'Thanks *{user.slack_username}*! {random.choice(congrats)}',
		)
	
	if params[0] == "past_scores":
		return_text = ''
		try:
			scores = user.set_scores.all()
			print(scores)
		except:
			return jsonify(
				response_type='ephemeral',
				text="You don't have any scores yet! Add one by using `*/set_score*`!"
				)

		for val in scores:
			print(val.value)
			return_text += f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n'

			print(f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n')

		return jsonify(
			type='section',
			response_type='ephemeral',
			text=f'Here are your past scores!\n{return_text}',
			)

	if params[0] == "compare_scores":
		if not params[1]:
			return jsonify(
				type='section',
				response_type='ephemeral',
				text="*Oops!* Looks like you didn't tell me who you'd like to compare yourself to. Try `compare_scores` followed by `<slack username>`"
				)
		compare_username = params[1]
		compare_user = User.query.filter_by(slack_username=compare_username).first()
		if not compare_user:
			return jsonify(
				type='section',
				response_type='ephemeral',
				text="*Oh no!* Either that's not a valid username, or that user hasn't played yet! Try again."
				)
		compare_user_scores = compare_user.set_scores.all()
		#user_df = pd.read_sql('SELECT * FROM User', db.session.bind)
		#scores_df = pd.read_sql('SELECT * FROM Score', db.session.bind)
		#merge_df = pd.merge(df, df1, left_on='id', right_on='user_id')
		#print(compare_user_scores)
		return jsonify(
			type='section',
			response_type='in_channel',
			text=f'{compare_user.slack_userid, compare_user.slack_username}'
			)

	if params[0] == "my_best":
		scores = user.set_scores.order_by(Score.value).all()
		if scores:
			best_time = scores.pop(0)
			return_text = f"*{best_time.timestamp.strftime('%c')}* - {best_time.orig_input} \U0001F451 \n"
			for s in scores[1:5]:
				return_text += f"*{s.timestamp.strftime('%c')}* - {s.orig_input}\n"
			return jsonify(
				type="section",
				response_type="in_channel",
				text=f"Your best scores at set are ~ \n\n {return_text}",
			)
		else:
			return jsonify(
				type="ephemeral",
				response_type="in_channel",
				text="No scores found for you. Input your score using `/set score`.",
			)

	if params[0] == "today":
		todays_datetime = datetime(datetime.today().year, datetime.today().month, datetime.today().day)
		scores = Score.query.filter(Score.timestamp >= todays_datetime).order_by(Score.value).all()
		if scores:
			winner = scores.pop(0)
			return_text = f'*{winner.user.slack_username}:*   {winner.orig_input} \U0001F451 \n'
			print(return_text)
			for s in scores:
				return_text += f'*{s.user.slack_username}:*   {s.orig_input}\n'
			return jsonify(
				type='section',
				response_type='in_channel',
				text=f'So far today the scores are ~ \n\n {return_text}'
			       	)
		else:
			return jsonify(
				type='ephemeral',
				response_type='in_channel',
				text='No scores have been recorded yet today! Input your score using `/set score`.'
				)
