"""
Account Service

This microservice handles the lifecycle of Accounts
"""

# pylint: disable=unused-import
from flask import jsonify, request, make_response, abort, url_for  # noqa: F401
from service.models import Account
from service.common import status  # HTTP Status Codes
from . import app  # Import Flask application


############################################################
# Health Endpoint
############################################################


@app.route("/health")
def health():
    """Health Status"""
    return jsonify(dict(status="OK")), status.HTTP_200_OK


############################################################
# Root Index Endpoint
############################################################


@app.route("/")
def index():
    """Root URL response"""
    return (
        jsonify(
            name="Account REST API Service",
            version="1.0",
        ),
        status.HTTP_200_OK,
    )


############################################################
# Utility Function to Check Content-Type
############################################################


def check_content_type(media_type):
    """Checks that the media type is correct"""
    if request.headers.get("Content-Type") != media_type:
        abort(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            f"Content-Type must be {media_type}"
        )


############################################################
# Create a New Account
############################################################


@app.route("/accounts", methods=["POST"])
def create_account():
    """Creates an Account"""
    check_content_type("application/json")
    account_data = request.get_json()
    account = Account()
    account.deserialize(account_data)
    account.create()
    location = url_for("get_account", account_id=account.id, _external=True)
    return make_response(
        jsonify(account.serialize()),
        status.HTTP_201_CREATED,
        {"Location": location}
    )


############################################################
# List All Accounts
############################################################


@app.route("/accounts", methods=["GET"])
def list_accounts():
    """Returns all Accounts"""
    accounts = Account.all()
    results = [account.serialize() for account in accounts]
    return jsonify(results), status.HTTP_200_OK


############################################################
# Read a Single Account
############################################################


@app.route("/accounts/<int:account_id>", methods=["GET"])
def get_account(account_id):
    """Returns an Account by ID"""
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id {account_id} not found.")
    return jsonify(account.serialize()), status.HTTP_200_OK


############################################################
# Update an Existing Account
############################################################


@app.route("/accounts/<int:account_id>", methods=["PUT"])
def update_account(account_id):
    """Updates an Account"""
    check_content_type("application/json")
    account = Account.find(account_id)
    if not account:
        abort(status.HTTP_404_NOT_FOUND, f"Account with id {account_id} not found.")
    account.deserialize(request.get_json())
    account.update()
    return jsonify(account.serialize()), status.HTTP_200_OK


############################################################
# Delete an Account
############################################################


@app.route("/accounts/<int:account_id>", methods=["DELETE"])
def delete_account(account_id):
    """Deletes an Account"""
    account = Account.find(account_id)
    if account:
        account.delete()
    return "", status.HTTP_204_NO_CONTENT
