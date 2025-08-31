"""
Contract routes for Contract Management Platform
"""
import logging

from flask import (
    Blueprint,
    current_app,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required

from app import db
from app.models.client import Client
from app.models.contract import Contract
from app.services.contract_service import ContractService


logger = logging.getLogger(__name__)
contracts_bp = Blueprint("contracts", __name__)


@contracts_bp.route("/")
@login_required
def index():
    """Contracts list page"""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    try:
        contracts = ContractService.get_all_contracts(
            include_deleted=False, page=page, per_page=per_page
        )

        return render_template("contracts/index.html", contracts=contracts)

    except Exception as e:
        logger.error(f"Error loading contracts: {e}")
        flash("An error occurred while loading contracts.", "error")
        return render_template("contracts/index.html", contracts=None)


@contracts_bp.route("/search")
@login_required
def search():
    """Contract search page"""
    search_term = request.args.get("q", "")
    status_filter = request.args.get("status", "")
    client_filter = request.args.get("client_id", "")
    contract_type_filter = request.args.get("contract_type", "")
    date_from = request.args.get("date_from", "")
    date_to = request.args.get("date_to", "")
    expiring_soon = request.args.get("expiring_soon", "")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    try:
        # Build filters
        filters = {}
        if status_filter:
            filters["status"] = status_filter
        if client_filter:
            filters["client_id"] = int(client_filter)
        if contract_type_filter:
            filters["contract_type"] = contract_type_filter
        if date_from:
            filters["date_from"] = date_from
        if date_to:
            filters["date_to"] = date_to
        if expiring_soon:
            filters["expiring_soon"] = int(expiring_soon)

        # Perform search
        contracts = ContractService.search_contracts(
            search_term=search_term, filters=filters, page=page, per_page=per_page
        )

        # Get clients for filter dropdown
        clients = Client.query.all()

        return render_template(
            "contracts/search.html",
            contracts=contracts,
            search_term=search_term,
            filters=filters,
            clients=clients,
        )

    except Exception as e:
        logger.error(f"Error searching contracts: {e}")
        flash("An error occurred while searching contracts.", "error")
        return render_template("contracts/search.html", contracts=None)


@contracts_bp.route("/<int:contract_id>")
@login_required
def show(contract_id):
    """Show contract details"""
    try:
        # First, try to get the contract directly from the database
        contract = Contract.query.get(contract_id)

        if not contract:
            flash("Contract not found.", "error")
            return redirect(url_for("contracts.index"))

        # Check if contract is soft-deleted
        if contract.deleted_at:
            flash("Contract not found.", "error")
            return redirect(url_for("contracts.index"))

        # Log access with request data (optional)
        try:
            # Log access - table existence is handled by the model
            contract.log_access(
                user_id=current_user.id,
                access_type="view",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            db.session.commit()
        except Exception as access_error:
            # Log access error but don't fail the request
            current_app.logger.warning(f"Failed to log contract access: {access_error}")
            db.session.rollback()

        return render_template("contracts/show.html", contract=contract)

    except Exception as e:
        logger.error(f"Error showing contract {contract_id}: {e}")
        # Log the full traceback for debugging
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        flash("An error occurred while loading the contract.", "error")
        return redirect(url_for("contracts.index"))


@contracts_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create new contract"""
    from app.forms.contract_forms import ContractForm

    # Get clients first
    clients = Client.query.order_by(Client.name).all()

    # Create form with client choices
    form = ContractForm()
    form.client_id.choices = [(0, "Select a client...")] + [
        (c.id, c.name) for c in clients
    ]

    # Set default values for other select fields
    if not form.contract_type.data:
        form.contract_type.data = ""
    if not form.status.data:
        form.status.data = ""

    if form.validate_on_submit():
        # Additional validation for client_id
        if form.client_id.data == 0:
            flash("Please select a client.", "error")
            return render_template("contracts/new.html", form=form, clients=clients)

        try:
            # Get form data
            contract_data = {
                "title": form.title.data,
                "description": form.description.data,
                "client_id": form.client_id.data,
                "contract_type": form.contract_type.data,
                "status": form.status.data,
                "contract_value": form.contract_value.data,
                "effective_date": form.effective_date.data,
                "expiration_date": form.expiration_date.data,
                "renewal_date": form.renewal_date.data,
            }

            # Get uploaded file
            file = form.contract_file.data

            # Create contract
            contract = ContractService.create_contract(
                contract_data=contract_data, file=file, created_by=current_user.id
            )

            flash(f'Contract "{contract.title}" created successfully!', "success")
            return redirect(url_for("contracts.show", contract_id=contract.id))

        except Exception as e:
            logger.error(f"Error creating contract: {e}")
            flash(f"An error occurred while creating the contract: {str(e)}", "error")
    elif form.errors:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")

    # GET request or validation failed - show form
    return render_template("contracts/new.html", form=form, clients=clients)


@contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
def edit(contract_id):
    """Edit contract"""
    from app.forms.contract_forms import ContractForm

    try:
        contract = ContractService.get_contract_by_id(contract_id)

        if not contract:
            flash("Contract not found.", "error")
            return redirect(url_for("contracts.index"))

        # Get clients first
        clients = Client.query.order_by(Client.name).all()

        # Create form with client choices
        form = ContractForm(obj=contract)
        form.client_id.choices = [(0, "Select a client...")] + [
            (c.id, c.name) for c in clients
        ]

        # Set default values for other select fields if they're None
        if not form.contract_type.data:
            form.contract_type.data = ""
        if not form.status.data:
            form.status.data = ""

        if form.validate_on_submit():
            # Additional validation for client_id
            if form.client_id.data == 0:
                flash("Please select a client.", "error")
                return render_template(
                    "contracts/edit.html", contract=contract, form=form, clients=clients
                )

            # Get form data
            update_data = {
                "title": form.title.data,
                "description": form.description.data,
                "client_id": form.client_id.data,
                "contract_type": form.contract_type.data,
                "status": form.status.data,
                "contract_value": form.contract_value.data,
                "effective_date": form.effective_date.data,
                "expiration_date": form.expiration_date.data,
                "renewal_date": form.renewal_date.data,
            }

            # Get uploaded file if provided
            file = form.contract_file.data if form.contract_file.data else None

            # Update contract
            contract = ContractService.update_contract(
                contract_id=contract_id,
                update_data=update_data,
                updated_by=current_user.id,
                file=file,
            )

            flash(f'Contract "{contract.title}" updated successfully!', "success")
            return redirect(url_for("contracts.show", contract_id=contract.id))
        elif form.errors:
            # Form validation failed
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{getattr(form, field).label.text}: {error}", "error")

        # GET request or validation failed - show edit form
        return render_template(
            "contracts/edit.html", contract=contract, form=form, clients=clients
        )

    except Exception as e:
        logger.error(f"Error editing contract {contract_id}: {e}")
        flash("An error occurred while editing the contract.", "error")
        return redirect(url_for("contracts.index"))


@contracts_bp.route("/<int:contract_id>/delete", methods=["POST"])
@login_required
def delete(contract_id):
    """Soft delete contract"""
    try:
        contract = ContractService.soft_delete_contract(contract_id, current_user)

        flash(f'Contract "{contract.title}" has been deleted.', "success")
        return redirect(url_for("contracts.index"))

    except Exception as e:
        logger.error(f"Error deleting contract {contract_id}: {e}")
        flash("An error occurred while deleting the contract.", "error")
        return redirect(url_for("contracts.show", contract_id=contract_id))


@contracts_bp.route("/<int:contract_id>/restore", methods=["POST"])
@login_required
def restore(contract_id):
    """Restore soft-deleted contract"""
    try:
        contract = ContractService.restore_contract(contract_id, current_user)

        flash(f'Contract "{contract.title}" has been restored.', "success")
        return redirect(url_for("contracts.show", contract_id=contract.id))

    except Exception as e:
        logger.error(f"Error restoring contract {contract_id}: {e}")
        flash("An error occurred while restoring the contract.", "error")
        return redirect(url_for("contracts.index"))


@contracts_bp.route("/<int:contract_id>/status", methods=["POST"])
@login_required
def update_status(contract_id):
    """Update contract status"""
    try:
        new_status = request.form.get("status")
        reason = request.form.get("reason", "")

        if not new_status:
            flash("Status is required.", "error")
            return redirect(url_for("contracts.show", contract_id=contract_id))

        contract = ContractService.update_contract_status(
            contract_id=contract_id,
            new_status=new_status,
            changed_by=current_user,
            reason=reason,
        )

        flash(f"Contract status updated to {new_status}.", "success")
        return redirect(url_for("contracts.show", contract_id=contract.id))

    except Exception as e:
        logger.error(f"Error updating contract status {contract_id}: {e}")
        flash("An error occurred while updating the contract status.", "error")
        return redirect(url_for("contracts.show", contract_id=contract_id))


@contracts_bp.route("/<int:contract_id>/download")
@login_required
def download(contract_id):
    """Download contract file"""
    try:
        contract = ContractService.get_contract_by_id(contract_id)

        if not contract or not contract.file_path:
            flash("Contract file not found.", "error")
            return redirect(url_for("contracts.show", contract_id=contract_id))

        # Security check: Ensure file path is within upload folder
        import os

        from flask import abort, current_app, send_file

        upload_folder = current_app.config.get("UPLOAD_FOLDER", "uploads")
        file_path = contract.file_path

        # Convert relative path to absolute path
        if not os.path.isabs(file_path):
            # If the path starts with 'uploads/', remove it to avoid duplication
            if file_path.startswith("uploads/"):
                file_path = file_path[8:]  # Remove 'uploads/' prefix
            file_path = os.path.join(upload_folder, file_path)

        # Debug logging
        logger.info(f"Original file_path from DB: {contract.file_path}")
        logger.info(f"Upload folder: {upload_folder}")
        logger.info(f"Resolved file_path: {file_path}")
        logger.info(f"File exists: {os.path.exists(file_path)}")

        # Normalize paths to prevent directory traversal attacks
        abs_upload_folder = os.path.abspath(upload_folder)
        abs_file_path = os.path.abspath(file_path)

        if not abs_file_path.startswith(abs_upload_folder):
            logger.error(
                f"Security violation: Attempted to access file outside upload folder: {file_path}"
            )
            abort(403, description="Access denied")

        # Check if file exists
        if not os.path.exists(file_path):
            logger.error(f"File not found on server: {file_path}")
            flash(
                "File not found on server. The file may have been moved or deleted.",
                "error",
            )
            return redirect(url_for("contracts.show", contract_id=contract_id))

        # Check if file is readable
        if not os.access(file_path, os.R_OK):
            logger.error(f"File not readable: {file_path}")
            flash("File access denied. Please contact an administrator.", "error")
            return redirect(url_for("contracts.show", contract_id=contract_id))

        # Log download access (optional - don't fail download if logging fails)
        try:
            contract.log_access(
                user_id=current_user.id,
                access_type="download",
                ip_address=request.remote_addr,
                user_agent=request.user_agent.string,
            )
            db.session.commit()
        except Exception as access_error:
            logger.warning(f"Failed to log download access: {access_error}")
            # Continue with download even if logging fails
            db.session.rollback()

        # Determine MIME type for proper browser handling
        mime_type = contract.mime_type or "application/octet-stream"

        # Set filename for download (use original filename if available)
        filename = contract.file_name or os.path.basename(file_path)

        # Send file with proper headers
        return send_file(
            file_path, as_attachment=True, download_name=filename, mimetype=mime_type
        )

    except Exception as e:
        logger.error(f"Error downloading contract {contract_id}: {e}")
        flash("An error occurred while downloading the contract.", "error")
        return redirect(url_for("contracts.show", contract_id=contract_id))


@contracts_bp.route("/deleted")
@login_required
def deleted():
    """Show deleted contracts"""
    if not current_user.is_admin:
        flash("Access denied. Admin privileges required.", "error")
        return redirect(url_for("contracts.index"))

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)

    try:
        contracts = ContractService.get_all_contracts(
            include_deleted=True, page=page, per_page=per_page
        )

        return render_template("contracts/deleted.html", contracts=contracts)

    except Exception as e:
        logger.error(f"Error loading deleted contracts: {e}")
        flash("An error occurred while loading deleted contracts.", "error")
        return render_template("contracts/deleted.html", contracts=None)


@contracts_bp.route("/api/search")
@login_required
def api_search():
    """API endpoint for contract search"""
    try:
        search_term = request.args.get("q", "")
        page = request.args.get("page", 1, type=int)
        per_page = request.args.get("per_page", 10, type=int)

        contracts = ContractService.search_contracts(
            search_term=search_term, page=page, per_page=per_page
        )

        # Convert to JSON-serializable format
        results = []
        for contract in contracts.items:
            results.append(contract.to_dict())

        return jsonify(
            {
                "contracts": results,
                "total": contracts.total,
                "pages": contracts.pages,
                "current_page": contracts.page,
                "has_next": contracts.has_next,
                "has_prev": contracts.has_prev,
            }
        )

    except Exception as e:
        logger.error(f"Error in API search: {e}")
        return jsonify({"error": "Search failed"}), 500
