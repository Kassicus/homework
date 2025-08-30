"""
Contract forms using Flask-WTF
"""
from datetime import date
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import (StringField, TextAreaField, SelectField, DecimalField, 
                    DateField, SubmitField, HiddenField)
from wtforms.validators import DataRequired, Length, Optional, NumberRange


class ContractForm(FlaskForm):
    """Contract creation/editing form"""
    title = StringField('Contract Title', validators=[
        DataRequired(message='Contract title is required'),
        Length(min=1, max=300, message='Title must be between 1 and 300 characters')
    ])
    
    description = TextAreaField('Description', validators=[
        Optional(),
        Length(max=2000, message='Description must be less than 2000 characters')
    ])
    
    client_id = SelectField('Client', coerce=int, validators=[
        DataRequired(message='Please select a client')
    ])
    
    contract_type = SelectField('Contract Type', choices=[
        ('', 'Select contract type...'),
        ('Service', 'Service Agreement'),
        ('Employment', 'Employment Contract'),
        ('Lease', 'Lease Agreement'),
        ('Purchase', 'Purchase Agreement'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('Partnership', 'Partnership Agreement'),
        ('Other', 'Other')
    ], validators=[
        DataRequired(message='Please select a contract type')
    ])
    
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed')
    ], validators=[
        DataRequired(message='Please select a status')
    ])
    
    contract_value = DecimalField('Contract Value', validators=[
        Optional(),
        NumberRange(min=0, message='Contract value must be positive')
    ])
    
    effective_date = DateField('Effective Date', validators=[Optional()])
    expiration_date = DateField('Expiration Date', validators=[Optional()])
    renewal_date = DateField('Renewal Date', validators=[Optional()])
    
    # File upload fields
    contract_file = FileField('Contract Document', validators=[
        Optional(),
        FileAllowed(['pdf', 'doc', 'docx', 'txt', 'rtf'], 
                   message='Only PDF, Word, and text files are allowed')
    ])
    
    submit = SubmitField('Save Contract')
    save_and_continue = SubmitField('Save & Continue')


class ContractSearchForm(FlaskForm):
    """Contract search form"""
    query = StringField('Search', validators=[
        Optional(),
        Length(min=2, message='Search query must be at least 2 characters')
    ])
    
    status = SelectField('Status', choices=[
        ('', 'All Statuses'),
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed')
    ])
    
    contract_type = SelectField('Contract Type', choices=[
        ('', 'All Types'),
        ('Service', 'Service Agreement'),
        ('Employment', 'Employment Contract'),
        ('Lease', 'Lease Agreement'),
        ('Purchase', 'Purchase Agreement'),
        ('NDA', 'Non-Disclosure Agreement'),
        ('Partnership', 'Partnership Agreement'),
        ('Other', 'Other')
    ])
    
    client_id = SelectField('Client', coerce=int, choices=[('', 'All Clients')])
    
    date_from = DateField('From Date', validators=[Optional()])
    date_to = DateField('To Date', validators=[Optional()])
    
    search_submit = SubmitField('Search')
    export_submit = SubmitField('Export Results')


class ContractStatusForm(FlaskForm):
    """Contract status change form"""
    new_status = SelectField('New Status', choices=[
        ('draft', 'Draft'),
        ('under_review', 'Under Review'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('terminated', 'Terminated'),
        ('renewed', 'Renewed')
    ], validators=[
        DataRequired(message='Please select a new status')
    ])
    
    change_reason = TextAreaField('Reason for Change', validators=[
        Optional(),
        Length(max=500, message='Reason must be less than 500 characters')
    ])
    
    submit = SubmitField('Update Status')
