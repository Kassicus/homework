"""
Authentication routes for Contract Management Platform
"""
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.urls import url_parse

from app.forms.auth_forms import LoginForm, RegistrationForm
from app.models.user import User
from app.services.auth_service import AuthService


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """User login page"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = LoginForm()

    if form.validate_on_submit():
        try:
            user = AuthService.authenticate_user(form.username.data, form.password.data)

            if user:
                login_user(user, remember=form.remember_me.data)

                # Log successful login
                current_app.logger.info(
                    f"User logged in successfully: {form.username.data}"
                )

                # Redirect to next page or dashboard
                next_page = request.args.get("next")
                if not next_page or url_parse(next_page).netloc != "":
                    next_page = url_for("dashboard.index")

                flash(f"Welcome back, {user.username}!", "success")
                return redirect(next_page)
            else:
                flash("Invalid username or password.", "error")

        except Exception as e:
            current_app.logger.error(f"Login error for user {form.username.data}: {e}")
            flash("An error occurred during login. Please try again.", "error")

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    """User logout"""
    username = current_user.username
    logout_user()

    current_app.logger.info(f"User logged out: {username}")
    flash("You have been logged out successfully.", "info")

    return redirect(url_for("auth.login"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """User registration page"""
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = RegistrationForm()

    if form.validate_on_submit():
        try:
            # Check if username or email already exists
            if User.query.filter_by(username=form.username.data).first():
                flash(
                    "Username already exists. Please choose a different one.", "error"
                )
                return render_template("auth/register.html", form=form)

            if User.query.filter_by(email=form.email.data).first():
                flash("Email already exists. Please use a different one.", "error")
                return render_template("auth/register.html", form=form)

            # Create new user
            AuthService.register_user(
                form.username.data, form.email.data, form.password.data
            )

            current_app.logger.info(
                f"New user registered: {form.username.data} ({form.email.data})"
            )

            flash("Registration successful! Please log in.", "success")
            return redirect(url_for("auth.login"))

        except Exception as e:
            current_app.logger.error(
                f"Registration error for user {form.username.data}: {e}"
            )
            flash("An error occurred during registration. Please try again.", "error")

    return render_template("auth/register.html", form=form)


@auth_bp.route("/profile")
@login_required
def profile():
    """User profile page"""
    return render_template("auth/profile.html")


@auth_bp.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    """Change password page"""
    from app.forms.auth_forms import ChangePasswordForm

    form = ChangePasswordForm()

    if form.validate_on_submit():
        try:
            AuthService.change_password(
                current_user.id, form.current_password.data, form.new_password.data
            )

            flash("Password changed successfully!", "success")
            return redirect(url_for("auth.profile"))

        except ValueError as e:
            flash(str(e), "error")
        except Exception as e:
            current_app.logger.error(
                f"Password change error for user {current_user.username}: {e}"
            )
            flash(
                "An error occurred while changing password. Please try again.", "error"
            )
    elif form.errors:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")

    return render_template("auth/change_password.html", form=form)


@auth_bp.route("/reset-password", methods=["GET", "POST"])
def reset_password():
    """Password reset page"""
    from app.forms.auth_forms import ResetPasswordForm

    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    form = ResetPasswordForm()

    if form.validate_on_submit():
        try:
            # Generate temporary password
            AuthService.reset_password(form.email.data)

            current_app.logger.info(
                f"Password reset requested for email: {form.email.data}"
            )

            # TODO: Send email with temporary password
            flash(
                "If an account with that email exists, a temporary password has been sent.",
                "info",
            )
            return redirect(url_for("auth.login"))

        except ValueError:
            # Don't reveal if email exists or not
            flash(
                "If an account with that email exists, a temporary password has been sent.",
                "info",
            )
            return redirect(url_for("auth.login"))
        except Exception as e:
            current_app.logger.error(
                f"Password reset error for email {form.email.data}: {e}"
            )
            flash("An error occurred during password reset. Please try again.", "error")
    elif form.errors:
        # Form validation failed
        for field, errors in form.errors.items():
            for error in errors:
                flash(f"{getattr(form, field).label.text}: {error}", "error")

    return render_template("auth/reset_password.html", form=form)
