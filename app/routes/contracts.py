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
from app.services.file_service import FileService

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
        contract = ContractService.get_contract_by_id(contract_id)

        if not contract:
            flash("Contract not found.", "error")
            return redirect(url_for("contracts.index"))

        return render_template("contracts/show.html", contract=contract)

    except Exception as e:
        logger.error(f"Error showing contract {contract_id}: {e}")
        flash("An error occurred while loading the contract.", "error")
        return redirect(url_for("contracts.index"))


@contracts_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    """Create new contract"""
    if request.method == "POST":
        try:
            # Get form data
            contract_data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "client_id": int(request.form.get("client_id")),
                "contract_type": request.form.get("contract_type"),
                "status": request.form.get("status", Contract.STATUS_DRAFT),
                "contract_value": request.form.get("contract_value"),
                "created_date": request.form.get("created_date"),
                "effective_date": request.form.get("effective_date"),
                "expiration_date": request.form.get("expiration_date"),
                "renewal_date": request.form.get("renewal_date"),
            }

            # Validate required fields
            if (
                not contract_data["title"]
                or not contract_data["client_id"]
                or not contract_data["contract_type"]
            ):
                flash("Title, client, and contract type are required.", "error")
                return render_template("contracts/new.html")

            # Get uploaded file
            file = request.files.get("contract_file")

            # Create contract
            contract = ContractService.create_contract(
                contract_data=contract_data, file=file, created_by=current_user
            )

            flash(f'Contract "{contract.title}" created successfully!', "success")
            return redirect(url_for("contracts.show", contract_id=contract.id))

        except Exception as e:
            logger.error(f"Error creating contract: {e}")
            flash(f"An error occurred while creating the contract: {str(e)}", "error")

    # GET request - show form
    clients = Client.query.all()
    return render_template("contracts/new.html", clients=clients)


@contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
def edit(contract_id):
    """Edit contract"""
    try:
        contract = ContractService.get_contract_by_id(contract_id)

        if not contract:
            flash("Contract not found.", "error")
            return redirect(url_for("contracts.index"))

        if request.method == "POST":
            # Get form data
            update_data = {
                "title": request.form.get("title"),
                "description": request.form.get("description"),
                "client_id": int(request.form.get("client_id")),
                "contract_type": request.form.get("contract_type"),
                "status": request.form.get("status"),
                "contract_value": request.form.get("contract_value"),
                "created_date": request.form.get("created_date"),
                "effective_date": request.form.get("effective_date"),
                "expiration_date": request.form.get("expiration_date"),
                "renewal_date": request.form.get("renewal_date"),
            }

            # Update contract
            contract = ContractService.update_contract(
                contract_id=contract_id,
                update_data=update_data,
                updated_by=current_user,
            )

            flash(f'Contract "{contract.title}" updated successfully!', "success")
            return redirect(url_for("contracts.show", contract_id=contract.id))

        # GET request - show edit form
        clients = Client.query.all()
        return render_template(
            "contracts/edit.html", contract=contract, clients=clients
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

        # Log download access
        contract.log_access(
            user_id=current_user.id,
            access_type="download",
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string,
        )
        db.session.commit()

        # TODO: Implement secure file download
        # For now, just redirect to file path
        flash("Download functionality not yet implemented.", "info")
        return redirect(url_for("contracts.show", contract_id=contract_id))

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
