# coding=utf-8
"""
Exposes a simple HTTP API to search a users Gists via a regular expression.

Github provides the Gist service as a pastebin analog for sharing code and
other develpment artifacts.  See http://gist.github.com for details.  This
module implements a Flask server exposing two endpoints: a simple ping
endpoint to verify the server is up and responding and a search endpoint
providing a search across all public Gists for a given Github account.
"""

import requests
import re
from flask import Flask, jsonify, request


# *The* app object
app = Flask(__name__)


@app.route("/ping")
def ping():
    """Provide a static response to a simple GET request."""
    return "pong"


def gists_for_user(username):
    """Provides the list of gist metadata for a given user.

    This abstracts the /users/:username/gist endpoint from the Github API.
    See https://developer.github.com/v3/gists/#list-a-users-gists for
    more information.

    Args:
        username (string): the user to query gists for

    Returns:
        The dict parsed from the json response from the Github API.  See
        the above URL for details of the expected structure.
    """
    gists_url = f"https://api.github.com/users/{username}/gists"
    response = requests.get(gists_url)
    # BONUS: What failures could happen? HTTP errors, 4XX,5XX,3XX
    # BONUS: Paging? How does this work for users with tons of gists?

    """
     can use query params to loop through pages. eg
     response_gists = []
     for i in range(30): #with 100 items per page the max pages is 30
       gists_url = https://api.github.com/users/{username}/gists?per_page=100&page={i}
       response_gists.append(requests.get(gists_url))
    """

    if response.status_code == 200 and response.json() != []:
        return {"status_success": True, "result": response.json()}
    elif response.status_code == 404:
        return {"status_success": False, "result": "404 Error. User does not exist"}
    elif response.status_code == 200 and response.json() == []:
        return {
            "status_success": False,
            "result": " Warning. The user does not have any public gists",
        }
    else:  # general invalid argument, can be improved with better error status catching
        return {"status_success": False, "result": "Error. Invalid username argument"}


@app.route("/api/v1/search", methods=["POST"])
def search():
    """Provides matches for a single pattern across a single users gists.

    Pulls down a list of all gists for a given user and then searches
    each gist for a given regular expression.

    Returns:
        A Flask Response object of type application/json.  The result
        object contains the list of matches along with a 'status' key
        indicating any failure conditions.
    """
    post_data = request.get_json()
    # BONUS: Validate the arguments? Check if empty
    if post_data != None:
        username = post_data["username"]
        pattern = post_data["pattern"]
    else:
        return "Error. Username and pattern has to be provided"

    result = {}
    result["matches"] = []
    gist_response = gists_for_user(username)
    if gist_response["status_success"]:
        gists = gist_response["result"]
    else:
        return gist_response["result"]
    # BONUS: Handle invalid users? hanled at gists_for_user function.
    # any invalid user will not generate a valid 200 response with data

    for gist in gists:
        # REQUIRED: Fetch each gist and check for the pattern
        # BONUS: What about huge gists?
        # BONUS: Can we cache results in a datastore/db?
        if not gist["truncated"]:  # not truncated, process file
            for file_obj in gist["files"]:
                file_contents = requests.get(gist["files"][file_obj]["raw_url"])
                if re.match(pattern, file_contents.text):
                    result["matches"].append(gist["html_url"])

        else:  # truncated hence huge gist and requres to be git pulled
            # cache results in datastore such as sqlite
            pass

    result["status"] = "success"
    result["username"] = username
    result["pattern"] = pattern
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=9876)
