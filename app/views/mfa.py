# ---------------------------------------------------------------------
# mfa.py
# app/views/mfa.py
# Blueprint for rendering the mfa page in Grylli.
# ---------------------------------------------------------------------

import base64
import io
import json
import secrets

import pyotp
import qrcode
from flask import (
    Blueprint,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from flask_babel import _
from flask_login import current_user, login_required
from flask_wtf import FlaskForm

from app.extensions import db
from app.forms.mfa_form import MFAChallengeForm, MFASettingsForm
from app.models import User
from app.services.encryption import decrypt, encrypt
from app.utils.logging import log_exception_with_traceback, log_info_message, log_user_action

bp = Blueprint("mfa", __name__, url_prefix="/mfa")


# ---------------------------------------------------------------------
# Generate recovery codes
# ---------------------------------------------------------------------
def generate_recovery_codes(count=10, length=8):
    """Generate a list of unique recovery codes."""
    codes = []
    while len(codes) < count:
        code = secrets.token_hex(length // 2).upper()
        if code not in codes:
            codes.append(code)
    return codes


# ---------------------------------------------------------------------
# Enable, disable, update MFA (HTMX-aware)
# ---------------------------------------------------------------------
@bp.route("", methods=["GET", "POST"], strict_slashes=False)
@login_required
def mfa_settings():
    """
    Enable, disable, or update MFA from a single settings form.
    Renders a partial if request is HTMX, otherwise full layout.
    """
    form = MFASettingsForm()
    initial_enabled = bool(current_user.mfa_enabled)

    try:
        if form.validate_on_submit():
            if form.enabled.data:
                if not initial_enabled or not current_user.mfa_enabled:
                    if not form.code.data:
                        flash(_("You must enter a code from your authenticator."), "danger")
                        log_info_message(
                            f"User '{current_user.username}' tried to enable MFA without a code."
                        )
                    else:
                        totp = pyotp.TOTP(current_user.mfa_secret)
                        if totp.verify(form.code.data):
                            current_user.mfa_enabled = True
                            recovery_codes = generate_recovery_codes()
                            current_user.mfa_recovery_codes = encrypt(json.dumps(recovery_codes))
                            current_user.mfa_recovery_codes_delivered = False
                            db.session.commit()
                            log_info_message(f"User '{current_user.username}' enabled MFA.")
                            log_user_action(
                                "Account", "Enable", "MFA enabled and recovery codes generated"
                            )
                            return redirect(url_for("mfa.show_recovery_codes"))
                        flash(_("Invalid code. Please try again."), "danger")
                        log_info_message(
                            f"User '{current_user.username}' provided invalid TOTP code."
                        )
            else:
                current_user.mfa_enabled = False
                current_user.mfa_secret = None
                current_user.mfa_recovery_codes = None
                db.session.commit()
                flash(_("Two-factor authentication disabled."), "info")
                log_info_message(f"User '{current_user.username}' disabled MFA.")
                log_user_action("Account", "Disable", "MFA disabled by user")
                return redirect(url_for("home.index"))

        if not current_user.mfa_secret:
            log_info_message(
                f"User '{current_user.username}' had no MFA secret; generating new one."
            )
            current_user.mfa_secret = pyotp.random_base32()
            db.session.commit()
            log_info_message(f"User '{current_user.username}' assigned new MFA secret.")
    except Exception as e:
        log_exception_with_traceback("Error during MFA settings update", e)
        flash(_("An unexpected error occurred while updating MFA settings."), "danger")
        return redirect(url_for("home.index"))

    secret = current_user.mfa_secret
    totp = pyotp.TOTP(secret)
    provisioning_url = totp.provisioning_uri(name=current_user.email, issuer_name="Grylli")
    img = qrcode.make(provisioning_url)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    qr_b64 = base64.b64encode(buf.read()).decode("utf-8")

    if request.method == "GET":
        form.enabled.data = initial_enabled
        log_info_message(f"Access - {current_user.username} - MFA Settings")

    template = (
        "mfa/settings_partial.html"
        if request.headers.get("HX-Request") == "true"
        else "mfa/settings_full.html"
    )

    return render_template(
        template,
        form=form,
        mfa_enabled=current_user.mfa_enabled,
        qr_b64=qr_b64,
        secret=secret,
    )


# ---------------------------------------------------------------------
# Show recovery codes
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# Show recovery codes
# ---------------------------------------------------------------------
@bp.route("recovery-codes", methods=["GET", "POST"], strict_slashes=False)
@login_required
def show_recovery_codes():
    """
    Show recovery codes once after enabling MFA, then mark as delivered.
    """
    if current_user.mfa_recovery_codes_delivered or not current_user.mfa_recovery_codes:
        flash(_("Recovery codes are only shown immediately after enabling MFA."), "warning")
        log_info_message(
            f"User '{current_user.username}' attempted to view MFA recovery codes but access was denied."
        )
        return redirect(url_for("home.index"))

    try:
        codes = json.loads(decrypt(current_user.mfa_recovery_codes))
        log_info_message(f"Access - {current_user.username} - MFA Recovery Codes")
        log_user_action("Account", "View", "Viewed MFA recovery codes")
    except Exception as exc:
        log_exception_with_traceback(
            f"User '{current_user.username}' failed to decrypt recovery codes during MFA challenge",
            exc,
        )
        flash(_("Could not load recovery codes."), "danger")
        return redirect(url_for("home.index"))

    if request.method == "POST":
        current_user.mfa_recovery_codes_delivered = True
        db.session.commit()
        log_info_message(f"User '{current_user.username}' marked MFA recovery codes as delivered.")
        log_user_action("Account", "Edit", "Marked MFA recovery codes as delivered")
        return redirect(url_for("home.index"))

    return render_template("mfa/recovery_codes.html", recovery_codes=codes, form=FlaskForm())


# ---------------------------------------------------------------------
# MFA Challenge
# ---------------------------------------------------------------------
# ---------------------------------------------------------------------
# MFA Challenge
# ---------------------------------------------------------------------
@bp.route("challenge", methods=["GET", "POST"], strict_slashes=False)
def mfa_challenge():
    """
    MFA Challenge: User must enter TOTP or recovery code to proceed.
    """
    pending_user_id = session.get("pending_mfa_user_id")
    if not pending_user_id:
        log_info_message("MFA challenge attempted without pending user session.")
        flash(_("No MFA challenge in progress."), "danger")
        return redirect(url_for("auth.login"))

    log_info_message(f"MFA challenge started for user ID={pending_user_id}")

    user = db.session.get(User, pending_user_id)
    if not user:
        log_info_message(f"MFA challenge failed: user ID={pending_user_id} not found.")
        flash(_("User not found for MFA challenge."), "danger")
        session.pop("pending_mfa_user_id", None)
        return redirect(url_for("auth.login"))

    form = MFAChallengeForm()
    error = None

    if form.validate_on_submit():
        try:
            code = form.code.data.strip()

            # Try as TOTP
            if code and user.mfa_secret:
                totp = pyotp.TOTP(user.mfa_secret)
                if totp.verify(code):
                    session.pop("pending_mfa_user_id", None)
                    session.pop("pending_mfa_next", None)
                    from flask_login import login_user

                    login_user(user)
                    flash(_("Logged in successfully."), "success")
                    log_info_message(f"User '{user.username}' passed TOTP MFA.")
                    log_user_action("Account", "Login", "Passed TOTP MFA")
                    next_page = session.pop("pending_mfa_next", None)
                    if next_page:
                        return redirect(next_page)
                    return redirect(url_for("home.index"))

            # Try as recovery code
            if user.mfa_recovery_codes:
                try:
                    codes = json.loads(decrypt(user.mfa_recovery_codes))
                except Exception as exc:
                    codes = []
                    log_exception_with_traceback(
                        "Failed to decrypt recovery codes during MFA challenge", exc
                    )

                if code in codes:
                    codes.remove(code)
                    from flask_login import login_user

                    if not codes:
                        # Last code used — disable MFA
                        user.mfa_enabled = False
                        user.mfa_secret = None
                        user.mfa_recovery_codes = None
                        user.mfa_recovery_codes_delivered = False
                        db.session.commit()
                        session.pop("pending_mfa_user_id", None)
                        session.pop("pending_mfa_next", None)
                        log_info_message(
                            f"User '{user.username}' used last recovery code. MFA disabled."
                        )
                        log_user_action(
                            "Account", "Login", "Used last MFA recovery code; MFA disabled"
                        )
                        login_user(user)
                        flash(
                            _(
                                "You have used your last recovery code. "
                                "MFA has been disabled. Please remove Grylli from your authenticator app, "
                                "and re-enable MFA to protect your account."
                            ),
                            "warning",
                        )
                        return redirect(url_for("mfa.mfa_settings"))
                    else:
                        user.mfa_recovery_codes = encrypt(json.dumps(codes))
                        db.session.commit()
                        session.pop("pending_mfa_user_id", None)
                        session.pop("pending_mfa_next", None)
                        log_info_message(
                            f"User '{user.username}' used recovery code. {len(codes)} remaining."
                        )
                        log_user_action(
                            "Account", "Login", f"Used MFA recovery code; {len(codes)} remaining"
                        )
                        login_user(user)
                        flash(
                            _(
                                "Recovery code accepted. You have {remaining} recovery codes left."
                            ).format(remaining=len(codes)),
                            "info",
                        )
                        next_page = session.pop("pending_mfa_next", None)
                        if next_page:
                            return redirect(next_page)
                        return redirect(url_for("home.index"))

            # MFA failed
            log_info_message(f"User '{user.username}' failed MFA challenge with invalid code.")
            log_user_action("Account", "Login", "Failed MFA challenge")
            error = _("Invalid code. Please try again.")
        except Exception as e:
            log_exception_with_traceback("Error during MFA challenge processing", e)
            flash(_("An unexpected error occurred during MFA challenge."), "danger")
            return redirect(url_for("auth.login"))

    # fallback if POST with invalid data (e.g., fails validators)
    if form.is_submitted() and not form.validate():
        error = _("Invalid code. Please try again.")

    return render_template("mfa/challenge.html", form=form, error=error)
