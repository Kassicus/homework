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
        clients = Client.query.order_by(Client.name).all()
        return render_template("clients/index.html", clients=clients)

    except Exception as e:
        logger.error(f"Error loading clients: {e}")
        flash("An error occurred while loading clients.", "error")
        return render_template("clients/index.html", clients=[])


@clients_bp.route("/<int:client_id>")
@login_required
def show(client_id):
    """Show client details"""
    try:
        client = Client.query.get_or_404(client_id)
        return render_template("clients/show.html", client=client)

    except Exception as e:
        logger.error(f"Error showing client {client_id}: {e}")
        flash("An error occurred while loading the client.", "error")
        return redirect(url_for("clients.index"))


@clients_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create new client"""
    if request.method == "POST":
        try:
            # Get form data
            client = Client(
                name=request.form.get("name"),
                organization=request.form.get("organization"),
                email=request.form.get("email"),
                phone=request.form.get("phone"),
                address=request.form.get("address"),
            )

            # Validate required fields
            if not client.name:
                flash("Client name is required.", "error")
                return render_template("clients/new.html")

            # Check for duplicate names
            existing_client = Client.query.filter_by(name=client.name).first()
            if existing_client:
                flash("A client with that name already exists.", "error")
                return render_template("clients/new.html")

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

    # GET request - show form
    return render_template("clients/new.html")


@clients_bp.route("/<int:client_id>/edit", methods=["GET", "POST"])
@login_required
def edit(client_id):
    """Edit client"""
    try:
        client = Client.query.get_or_404(client_id)

        if request.method == "POST":
            # Update client data
            client.name = request.form.get("name")
            client.organization = request.form.get("organization")
            client.email = request.form.get("email")
            client.phone = request.form.get("phone")
            client.address = request.form.get("address")

            # Validate required fields
            if not client.name:
                flash("Client name is required.", "error")
                return render_template("clients/edit.html", client=client)

            # Check for duplicate names (excluding current client)
            existing_client = Client.query.filter(
                Client.name == client.name, Client.id != client.id
            ).first()
            if existing_client:
                flash("A client with that name already exists.", "error")
                return render_template("clients/edit.html", client=client)

            db.session.commit()

            current_app.logger.info(
                f"Client updated: {client.name} by user {current_user.username}"
            )

            flash(f'Client "{client.name}" updated successfully!', "success")
            return redirect(url_for("clients.show", client_id=client.id))

        # GET request - show edit form
        return render_template("clients/edit.html", client=client)

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
