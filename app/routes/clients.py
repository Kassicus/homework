"""
Client routes for Contract Management Platform
"""
import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.models.client import Client


logger = logging.getLogger(__name__)
clients_bp = Blueprint("clients", __name__)


@clients_bp.route("/")
@login_required
def index():
    """Clients list page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 20  # Show 20 clients per page
        
        # Use paginate() instead of all()
        clients = Client.query.order_by(Client.name).paginate(
            page=page, 
            per_page=per_page, 
            error_out=False
        )
        
        return render_template("clients/index.html", clients=clients)

    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        flash("An error occurred while loading clients.", "error")
        # Return empty pagination object on error
        from flask_sqlalchemy import Pagination
        empty_pagination = Pagination(Client.query, 1, 20, 0, [])
        return render_template("clients/index.html", clients=empty_pagination)


@clients_bp.route("/<int:client_id>")
@login_required
def show(client_id):
    """Show client details"""
    try:
        client = Client.query.get_or_404(client_id)
        
        # Get contracts for this client
        from app.models.contract import Contract
        contracts = Contract.query.filter_by(
            client_id=client_id, 
            deleted_at=None
        ).order_by(Contract.created_at.desc()).all()
        
        return render_template("clients/show.html", client=client, contracts=contracts)

    except Exception as e:
        logger.error(f"Error showing client {client_id}: {e}")
        flash("An error occurred while loading the client.", "error")
        return redirect(url_for("clients.index"))


@clients_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create new client"""
    from app.forms.client_forms import ClientForm
    
    form = ClientForm()
    
    if form.validate_on_submit():
        try:
            # Create client from form data
            client = Client(
                name=form.name.data,
                organization=form.organization.data,
                email=form.email.data,
                phone=form.phone.data,
                address=form.address.data,
            )

            # Check for duplicate names
            existing_client = Client.query.filter_by(name=client.name).first()
            if existing_client:
                flash("A client with that name already exists.", "error")
                return render_template("clients/new.html", form=form)

            db.session.add(client)
            db.session.commit()

            current_app.logger.info(
                f"New client created: {client.name} by user {current_user.username}"
            )

            flash(f'Client "{client.name}" created successfully!', "success")
            return redirect(url_for("clients.show", client_id=client.id))

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating client: {e}")
            flash("An error occurred while creating the client.", "error")
    elif form.errors:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")

    # GET request or validation failed - show form
    return render_template("clients/new.html", form=form)


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit(client_id):
    """Edit client"""
    from app.forms.client_forms import ClientForm
    
    try:
        client = Client.query.get_or_404(client_id)
        form = ClientForm(obj=client)

        if form.validate_on_submit():
            # Update client data from form
            client.name = form.name.data
            client.organization = form.organization.data
            client.email = form.email.data
            client.phone = form.phone.data
            client.address = form.address.data

            # Check for duplicate names (excluding current client)
            existing_client = Client.query.filter(
                Client.name == client.name, Client.id != client.id
            ).first()
            if existing_client:
                flash("A client with that name already exists.", "error")
                return render_template("clients/edit.html", client=client, form=form)

            db.session.commit()

            current_app.logger.info(
                f"Client updated: {client.name} by user {current_user.username}"
            )

            flash(f'Client "{client.name}" updated successfully!', "success")
            return redirect(url_for("clients.show", client_id=client.id))
        elif form.errors:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "error")

        # GET request or validation failed - show edit form
        return render_template("clients/edit.html", client=client, form=form)

    except Exception as e:
        logger.error(f"Error editing client {client_id}: {e}")
        flash("An error occurred while editing the client.", "error")
        return redirect(url_for("clients.index"))


@clients_bp.route("/<int:client_id>/delete", methods=["POST"])
@login_required
def delete(client_id):
    """Delete client (only if no contracts exist)"""
    try:
        client = Client.query.get_or_404(client_id)

        # Check if client has contracts
        if client.contracts.count() > 0:
            flash(
                f'Cannot delete client "{client.name}" because they have {client.contracts.count()} contract(s).',
                "error",
            )
            return redirect(url_for("clients.show", client_id=client.id))

        client_name = client.name
        db.session.delete(client)
        db.session.commit()

        current_app.logger.info(
            f"Client deleted: {client_name} by user {current_user.username}"
        )

        flash(f'Client "{client_name}" has been deleted.', "success")
        return redirect(url_for("clients.index"))

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting client {client_id}: {e}")
        flash("An error occurred while deleting the client.", "error")
        return redirect(url_for("clients.show", client_id=client_id))


@clients_bp.route("/search")
@login_required
def search():
    """Search clients"""
    search_term = request.args.get("q", "")

    try:
        if search_term:
            # Search by name or organization
            clients = (
                Client.query.filter(
                    db.or_(
                        Client.name.ilike(f"%{search_term}%"),
                        Client.organization.ilike(f"%{search_term}%"),
                    )
                )
                .order_by(Client.name)
                .all()
            )
        else:
            clients = []

        return render_template(
            "clients/search.html", clients=clients, search_term=search_term
        )

    except Exception as e:
        logger.error(f"Error searching clients: {e}")
        flash("An error occurred while searching clients.", "error")
        return render_template(
            "clients/search.html", clients=[], search_term=search_term
        )


@clients_bp.route("/api/search")
@login_required
def api_search():
    """API endpoint for client search"""
    try:
        search_term = request.args.get("q", "")

        if search_term:
            clients = (
                Client.query.filter(
                    db.or_(
                        Client.name.ilike(f"%{search_term}%"),
                        Client.organization.ilike(f"%{search_term}%"),
                    )
                )
                .limit(10)
                .all()
            )
        else:
            clients = []

        # Convert to JSON-serializable format
        results = []
        for client in clients:
            results.append(client.to_dict())

        return {"clients": results}

    except Exception as e:
        logger.error(f"Error in API client search: {e}")
        return {"error": "Search failed"}, 500
