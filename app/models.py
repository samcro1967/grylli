"""
# ---------------------------------------------------------------------
# models.py
# app/models.py
# SQLAlchemy ORM models for users, config, messages, notifications, and files.
# ---------------------------------------------------------------------
"""

from datetime import datetime

from sqlalchemy.sql import text
from werkzeug.security import check_password_hash

from app.extensions import db
from app.services.encryption import decrypt, encrypt


# ---------------------------------------------------------------------
# System Configuration
# ---------------------------------------------------------------------
class SystemConfig(db.Model):
    """
    Stores key-value pairs for application system settings and secrets.
    """

    __tablename__ = "system_config"
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(64), nullable=False, unique=True)
    value = db.Column(db.String(512), nullable=False)
    is_sensitive = db.Column(db.Boolean, default=False)
    editable = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return f"<SystemConfig {self.key} (sensitive={self.is_sensitive})>"


# ---------------------------------------------------------------------
# User Accounts
# ---------------------------------------------------------------------
class User(db.Model):
    """
    Represents a Grylli user account with login and notification settings.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    # Relationships
    messages = db.relationship("Message", back_populates="user")
    email_messages = db.relationship("EmailMessage", back_populates="user")
    smtp_configs = db.relationship("UserMailSettings", backref="user", cascade="all, delete-orphan")

    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(10), nullable=False)  # 'admin' or 'user'
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime(timezone=True),
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP"),
    )

    def get_id(self):
        """Return user ID as string (used by Flask-Login)."""
        return str(self.id)

    def check_password(self, password):
        """Validate a plaintext password against the stored hash."""
        return check_password_hash(self.password_hash, password)

    @property
    def is_authenticated(self):
        """Required for Flask-Login: always True for registered users."""
        return True

    @property
    def is_active(self):
        """Required for Flask-Login: always True for active users."""
        return True

    @property
    def is_anonymous(self):
        """Required for Flask-Login: always False for registered users."""
        return False

    @property
    def is_admin(self):
        """Returns True if the user is an admin."""
        return self.role == "admin"


# ---------------------------------------------------------------------
# Apprise Notification URLs
# ---------------------------------------------------------------------
class AppriseURL(db.Model):
    """
    Stores Apprise notification URLs for messaging.
    """

    __tablename__ = "apprise_urls"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    _url = db.Column("url", db.Text, nullable=False)
    enabled = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    @property
    def url(self):
        """Return the decrypted Apprise URL."""
        return decrypt(self._url)

    @url.setter
    def url(self, value):
        """Encrypt and set the Apprise URL."""
        self._url = encrypt(value)


# ---------------------------------------------------------------------
# Incoming Webhooks
# ---------------------------------------------------------------------
class Webhook(db.Model):
    """
    Stores incoming webhook endpoints for notification triggers.
    """

    __tablename__ = "webhooks"

    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(100), nullable=False)
    _endpoint = db.Column("endpoint", db.Text, unique=True, nullable=False)
    description = db.Column(db.Text)
    enabled = db.Column(db.Boolean, default=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    @property
    def endpoint(self):
        """Return the decrypted webhook endpoint."""
        return decrypt(self._endpoint)

    @endpoint.setter
    def endpoint(self, value):
        """Encrypt and set the webhook endpoint."""
        self._endpoint = encrypt(value)


# ---------------------------------------------------------------------
# Messages Table
# ---------------------------------------------------------------------
class Message(db.Model):
    """
    Represents a standard user message with check-in, expiry, and notification options.
    """

    __tablename__ = "messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="messages")
    label = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    checkin_interval_minutes = db.Column(db.Integer, nullable=True)
    grace_period_minutes = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_checkin = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)

    apprise_destinations = db.relationship(
        "AppriseURL", secondary="message_apprise_links", backref="messages"
    )
    webhooks = db.relationship("Webhook", secondary="message_webhook_links", backref="messages")


# ---------------------------------------------------------------------
# Messages → Apprise Join Table
# ---------------------------------------------------------------------
message_apprise_links = db.Table(
    "message_apprise_links",
    db.Column("message_id", db.Integer, db.ForeignKey("messages.id"), primary_key=True),
    db.Column("apprise_id", db.Integer, db.ForeignKey("apprise_urls.id"), primary_key=True),
)


# ---------------------------------------------------------------------
# Messages → Webhook Join Table
# ---------------------------------------------------------------------
message_webhook_links = db.Table(
    "message_webhook_links",
    db.Column("message_id", db.Integer, db.ForeignKey("messages.id"), primary_key=True),
    db.Column("webhook_id", db.Integer, db.ForeignKey("webhooks.id"), primary_key=True),
)


# ---------------------------------------------------------------------
# Secure Email Messages
# ---------------------------------------------------------------------
class EmailMessage(db.Model):
    """
    Stores email message records that will be delivered to recipients.
    """

    __tablename__ = "email_messages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    user = db.relationship("User", back_populates="email_messages")
    label = db.Column(db.String(100), nullable=False)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    recipient = db.Column(db.String(255), nullable=False)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        server_default=text("CURRENT_TIMESTAMP"),
    )
    checkin_interval_minutes = db.Column(db.Integer, nullable=False, server_default="0")
    grace_period_minutes = db.Column(db.Integer, nullable=False, server_default="0")
    last_checkin = db.Column(db.DateTime, nullable=True)
    executed_at = db.Column(db.DateTime, nullable=True)
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    is_enabled = db.Column(db.Boolean, nullable=False, default=False)

    smtp_configs = db.relationship(
        "UserMailSettings", secondary="email_smtp_links", backref="linked_secure_emails"
    )
    files = db.relationship("EmailFileLink", backref="message", cascade="all, delete-orphan")

    @property
    def is_created(self):
        """Return True if all required fields (subject, body, recipient) are present."""
        return bool(self.subject and self.body and self.recipient)

    @property
    def is_smtp_assigned(self):
        """Return True if one or more SMTP configs are linked."""
        return len(self.smtp_configs) > 0

    @property
    def is_scheduled(self):
        """Return True if both check-in and grace periods are > 0."""
        return (self.checkin_interval_minutes or 0) > 0 and (self.grace_period_minutes or 0) > 0


# ---------------------------------------------------------------------
# Secure Email → File Attachments Join Table
# ---------------------------------------------------------------------
class EmailFileLink(db.Model):
    """
    Stores file attachments for EmailMessage.
    """
    __tablename__ = "email_file_links"
    message_id = db.Column(db.Integer, db.ForeignKey("email_messages.id"), primary_key=True)
    file_path = db.Column(db.String(255), primary_key=True)


# ---------------------------------------------------------------------
# Per-User SMTP Configuration
# ---------------------------------------------------------------------
class UserMailSettings(db.Model):
    """
    Stores SMTP configuration for each user.
    """

    __tablename__ = "user_mail_settings"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    label = db.Column(db.String(100), nullable=False)
    smtp_host = db.Column(db.String(128), nullable=False)
    smtp_port = db.Column(db.Integer, nullable=False)
    smtp_username = db.Column(db.String(128), nullable=False)
    _smtp_password = db.Column("smtp_password", db.String(512), nullable=False)  # encrypted
    use_tls = db.Column(db.Boolean, default=True)
    enabled = db.Column(db.Boolean, default=True)
    created_at = db.Column(
        db.DateTime, default=datetime.utcnow, server_default=text("CURRENT_TIMESTAMP")
    )

    @property
    def smtp_password(self):
        """Return decrypted SMTP password."""
        return decrypt(self._smtp_password)

    @smtp_password.setter
    def smtp_password(self, value):
        """Encrypt and set the SMTP password."""
        self._smtp_password = encrypt(value)


# ---------------------------------------------------------------------
# Messages → SMTP Join Table
# ---------------------------------------------------------------------
email_smtp_links = db.Table(
    "email_smtp_links",
    db.Column("email_id", db.Integer, db.ForeignKey("email_messages.id"), primary_key=True),
    db.Column("smtp_id", db.Integer, db.ForeignKey("user_mail_settings.id"), primary_key=True),
)

# ---------------------------------------------------------------------
# End of file: app/models.py
# ---------------------------------------------------------------------
