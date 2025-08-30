"""
Client forms using Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional


class ClientForm(FlaskForm):
    """Client creation/editing form"""

    name = StringField(
        "Client Name",
        validators=[
            DataRequired(message="Client name is required"),
            Length(min=1, max=200, message="Name must be between 1 and 200 characters"),
        ],
    )

    organization = StringField(
        "Organization",
        validators=[
            Optional(),
            Length(max=200, message="Organization must be less than 200 characters"),
        ],
    )

    email = StringField(
        "Email",
        validators=[
            Optional(),
            Length(max=120, message="Email must be less than 120 characters"),
        ],
    )

    phone = StringField(
        "Phone",
        validators=[
            Optional(),
            Length(max=20, message="Phone must be less than 20 characters"),
        ],
    )

    address = TextAreaField(
        "Address",
        validators=[
            Optional(),
            Length(max=500, message="Address must be less than 500 characters"),
        ],
    )

    submit = SubmitField("Save Client")
    save_and_continue = SubmitField("Save & Continue")


class ClientSearchForm(FlaskForm):
    """Client search form"""

    query = StringField(
        "Search",
        validators=[
            Optional(),
            Length(min=2, message="Search query must be at least 2 characters"),
        ],
    )

    organization = StringField(
        "Organization",
        validators=[
            Optional(),
            Length(max=200, message="Organization must be less than 200 characters"),
        ],
    )

    search_submit = SubmitField("Search")
    export_submit = SubmitField("Export Results")
