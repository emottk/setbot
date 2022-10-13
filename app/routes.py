import os

from app import app, db
from app.models import User, Score
from flask import abort, jsonify, request
from sqlalchemy.sql.functions import min
import arrow
import random


def is_request_valid(request):
    is_token_valid = request.form["token"] == os.environ["SLACK_VERIFICATION_TOKEN"]
    is_team_id_valid = request.form["team_id"] == os.environ["SLACK_TEAM_ID"]

    return is_token_valid and is_team_id_valid


def get_user():
    user_id = request.form["user_id"]
    user_name = request.form["user_name"]

    user = User.query.filter_by(slack_userid=user_id).first()

    if not User.query.filter_by(slack_userid=user_id).first():
        user = User(slack_userid=user_id, slack_username=user_name)
        db.session.add(user)
        db.session.commit()

    return user


# def check_score_input(score):
# try:
# value = datetime.strptime(score, "%H hours %M minutes and %S.%f s\
# econds`").time()
#   except Exception as e:


@app.route("/set", methods=["POST"])
def set_score():
    if not is_request_valid(request):
        abort(400)

    commands = [
        "help",
        "score",
        "past_scores",
        "compare_scores",
        "today",
        "my_best",
        "top10",
        "leaderboard",
        "overview",
    ]
    text_input = request.form["text"]

    if text_input:
        params = text_input.split()
    else:
        return jsonify(
            response_type="ephemeral",
            type="section",
            text="I didn't catch that! Type 'help' for a list of appropriate commands",
        )

    if params[0] not in commands:
        return jsonify(
            response_type="ephemeral",
            type="section",
            text="I didn't catch that! Type 'help' for a list of appropriate commands",
        )

    if params[0] == "help":
        return command_help(params)

    if params[0] == "score":
        return command_score(params)

    if params[0] == "past_scores":
        return command_past_scores(params)

    if params[0] == "compare_scores":
        return command_compare_scores(params)

    if params[0] == "my_best":
        return command_my_best(params)

    if params[0] == "top10":
        return command_top10(params)

    if params[0] == "leaderboard":
        return command_leaderboard(params)

    if params[0] == "today":
        return command_today(params)

    if params[0] == "overview":
        return command_overview(params)


def command_help(*args, **kwargs):
    return jsonify(
        response_type="ephemeral",
        text=(
            "Here are some commands you can try:"
            + "\n *score* [set score format including backticks and hours]"
            + "\n *past_scores*"
            + "\n *compare_scores* [slack username]"
            + "\n *today*"
            + "\n my_best"
            + "\n top10"
            + "\n leaderboard"
            + "\n overview"
        ),
    )


def command_score(*args, **kwargs):
    user = get_user()
    text_input = request.form["text"]

    input_value = text_input.replace("*", "").split(" `")
    try:
        value = arrow.Arrow.strptime(
            input_value[1], "%H hours %M minutes and %S.%f seconds`"
        ).time()
    except Exception:
        return jsonify(
            response_type="ephemeral",
            text="*Uh oh*, I didn't catch that! Please input your score in a code block using backticks, in set score form ex: `0 hours 00 minutes and 0.00 seconds`",
        )
    score = Score(orig_input=f"`{input_value[1]}", user=user, value=value)
    db.session.add(score)
    db.session.commit()
    congrats = [
        "Good job!",
        "Well done!",
        "Very impressive.",
        "Something something blind dog sunshine something.",
    ]
    return jsonify(
        response_type="in_channel",
        text=f"Thanks *{user.slack_username}*! {random.choice(congrats)}",
    )


def command_past_scores(*args, **kwargs):
    user = get_user()
    return_text = ""
    try:
        scores = user.set_scores.all()
        print(scores)
    except Exception:
        return jsonify(
            response_type="ephemeral",
            text="You don't have any scores yet! Add one by using `*/set_score*`!",
        )

    for val in scores:
        print(val.value)
        return_text += f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n'

        print(
            f'{val.value.strftime("`%H hours %M minutes and %S.%f seconds`")} on *{val.timestamp.strftime("%c")}*\n'
        )

    return jsonify(
        type="section",
        response_type="ephemeral",
        text=f"Here are your past scores!\n{return_text}",
    )


def command_compare_scores(params, *args, **kwargs):

    if len(params) < 2:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="*Oops!* Looks like you didn't tell me who you'd like to compare yourself to. Try `compare_scores` followed by `<slack username>`",
        )
    compare_username = params[1]
    try:
        compare_timeframe = params[2]
    except IndexError:
        compare_timeframe = "best"
    compare_user = User.query.filter_by(slack_username=compare_username).first()
    user = get_user()
    if not compare_user:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="*Oh no!* Either that's not a valid username, or that user hasn't played yet! Try again.",
        )

    if compare_timeframe == "today":
        todays_datetime = (
            arrow.now("US/Pacific")
            .replace(hour=0, minute=0, second=0, microsecond=0)
            .datetime
        )
        their_score = (
            compare_user.set_scores.filter(Score.timestamp >= todays_datetime)
            .order_by(Score.value)
            .first()
        )
        user_score = (
            user.set_scores.filter(Score.timestamp >= todays_datetime)
            .order_by(Score.value)
            .first()
        )
    elif compare_timeframe == "best":
        their_score = compare_user.set_scores.order_by(Score.value).first()
        user_score = user.set_scores.order_by(Score.value).first()
    else:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="*Oops!* That's not a valid timeframe. "
            + "Try `compare_scores` followed by `<slack username> <best or today>`",
        )

    their_time = their_score.orig_input if their_score else "No time recorded"
    user_time = user_score.orig_input if user_score else "No time recorded"

    return_text = (
        f"*{user.slack_username}:*   {user_time}\n"
        + f"*{compare_user.slack_username}:*   {their_time}\n"
    )
    return jsonify(
        type="section",
        response_type="ephemeral",
        text=return_text,
    )


def command_my_best(*args, **kwargs):
    user = get_user()
    scores = user.set_scores.order_by(Score.value).all()
    if scores:
        best_time = scores.pop(0)
        return_text = f"*{best_time.timestamp.strftime('%c')}* - {best_time.orig_input} \U0001F451 \n"
        for s in scores[1:5]:
            return_text += f"*{s.timestamp.strftime('%c')}* - {s.orig_input}\n"
        return jsonify(
            type="section",
            response_type="ephemeral",
            text=f"Your best scores at set are ~ \n\n {return_text}",
        )
    else:
        return jsonify(
            type="section",
            response_type="in_channel",
            text="No scores found for you. Input your score using `/set score`.",
        )


def command_top10(*args, **kwargs):
    scores = Score.query.order_by(Score.value).all()
    if scores:
        best_time = scores.pop(0)
        return_text = f"*{best_time.timestamp.strftime('%c')}* - {best_time.user.slack_username} - {best_time.orig_input} \U0001F451 \n"
        for s in scores[0:9]:
            return_text += f"*{s.timestamp.strftime('%c')}* - {s.user.slack_username} - {s.orig_input}\n"
        return jsonify(
            type="section",
            response_type="ephemeral",
            text=f"Top 10 overall scores are ~ \n\n {return_text}",
        )
    else:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="No scores found yet. Input your score using `/set score`.",
        )


def command_leaderboard(*args, **kwargs):
    scores = (
        Score.query.group_by(Score.user_id)
        .having(min(Score.value) > 0)
        .order_by(Score.value)
        .all()
    )
    if scores:
        best_time = scores.pop(0)
        return_text = f"*{best_time.timestamp.strftime('%c')}* - {best_time.user.slack_username} - {best_time.orig_input} \U0001F451 \n"
        for s in scores[0:9]:
            return_text += f"*{s.timestamp.strftime('%c')}* - {s.user.slack_username} - {s.orig_input}\n"
        return jsonify(
            type="section",
            response_type="ephemeral",
            text=f"Top 10 Personal Bests are ~ \n\n {return_text}",
        )
    else:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="No scores found yet. Input your score using `/set score`.",
        )


def command_today(*args, **kwargs):
    todays_datetime = (
        arrow.now("US/Pacific")
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .datetime
    )
    scores = (
        Score.query.filter(Score.timestamp >= todays_datetime)
        .order_by(Score.value)
        .all()
    )
    if scores:
        winner = scores.pop(0)
        return_text = (
            f"*{winner.user.slack_username}:*   {winner.orig_input} \U0001F451 \n"
        )
        print(return_text)
        for s in scores:
            return_text += f"*{s.user.slack_username}:*   {s.orig_input}\n"
        return jsonify(
            type="section",
            response_type="in_channel",
            text=f"So far today the scores are ~ \n\n {return_text}",
        )
    else:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="No scores have been recorded yet today! Input your score using `/set score`.",
        )


def command_overview(params, *args, **kwargs):
    try:
        target_username = params[1]
        user = User.query.filter_by(slack_username=target_username).first()
    except IndexError:
        user = get_user()

    if not user or user.set_scores.count() < 1:
        return jsonify(
            type="section",
            response_type="ephemeral",
            text="No scores have been recorded yet for this user.",
        )


    first_time = user.set_scores.order_by(Score.timestamp).first()
    last_time = user.set_scores.order_by(Score.timestamp.desc()).first()
    fastest_time = user.set_scores.order_by(Score.value).first()
    slowest_time = user.set_scores.order_by(Score.value.desc()).first()

    return_text = (
        f"An overview of {user.slack_username}'s scores\n" +
        f"\nFirst: *{first_time.timestamp.strftime('%c')}* {first_time.orig_input}"
        f"\nLatest: *{last_time.timestamp.strftime('%c')}* {last_time.orig_input}"
        f"\nFastest: *{fastest_time.timestamp.strftime('%c')}* {fastest_time.orig_input}"
        f"\nSlowest: *{slowest_time.timestamp.strftime('%c')}* {slowest_time.orig_input}"
    )

    return jsonify(
        type="section",
        response_type="ephemeral",
        text=return_text,
    )
