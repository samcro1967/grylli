<p align="center">
  <img src="app/static/icons/grylli_icon_dark.png" alt="Grylli Logo" width="256">
</p>

# Grylli

Grylli is a secure, self-hosted message delivery platform that automatically sends pre-configured notifications if a user fails to check in within a defined time period.

---

## Features

### 🚀 Core Application
- **Self-hosted Flask web application** with user authentication
- **Responsive UI** built with Tailwind CSS
- Light and dark mode support
- Local timezone support
- Multilingual interface

### 🔔 Notifications & Messaging
- Configurable notification and check-in system
- Customizable emails with optional attachments and webhooks
- Attach multiple files to notifications
- Files are loaded from disk at send time (edit outside Grylli)
- Send notifications to 110+ destinations via [Apprise](https://github.com/caronc/apprise)

### 👤 User & Admin Management
- Multi-admin and multi-user support
- Sign up with registration code
- Forgot username, forgot password, and password reset flows
- CLI utility to reset admin password

### 🛡️ Security
- Sensitive data encrypted in the database
- Enforces complex passwords
- Runs as non-root using PUID/PGID
- Reverse proxy ready (`base_url` support)

### 📧 Email & Integrations
- Global SMTP settings
- User-specific SMTP settings (users can send emails from their own addresses)

### 💾 Backups & Maintenance
- Automated database backups (7-day retention)
- On-demand backup option

---

## Screenshots
<details>
  <summary><strong>Show Screenshots</strong></summary>
<img src="screenshots/login.png" alt="My Screenshot" width="400"/>
<img src="screenshots/home.png" alt="My Screenshot" width="400"/>
<img src="screenshots/admin.png" alt="My Screenshot" width="400"/>
<img src="screenshots/notifications.png" alt="My Screenshot" width="400"/>
<img src="screenshots/emails.png" alt="My Screenshot" width="400"/>
</details>

---
## Docker Compose Configuration
[`docker-compose.sample.yml`](./docker-compose.sample.yml)

If you prefer not to use Docker Compose, you can run Grylli with a single command:

<details>
  <summary><strong>Show Docker Run Command</strong></summary>
  
```
docker run -d \
  --name grylli \
  -p 5069:5069 \
  -v $(pwd)/grylli/data:/data \
  -v $(pwd)/grylli/uploads:/uploads \
  -e TZ=America/Chicago \
  -e PUID=1000 \
  -e PGID=1000 \
  -e GRYLLI_DATA_DIR=/data \
  -e DEBUG=False \
  -e FQDN=http://your.domain.com:5069 \
  -e BASE_URL=/grylli \
  -e FLASK_APP_PORT=5069 \
  -e FLASK_APP_KEY=changeme-supersecret-key \
  -e FERRET_KEY=changeme-fernet-key \
  -e SIGNUP_CODE=YourSuperSecretCode123! \
  -e DEFAULT_LANGUAGE=en \
  -e SMTP_HOST=smtp.example.com \
  -e SMTP_PORT=587 \
  -e SMTP_USE_TLS=1 \
  -e EMAIL_FROM=you@example.com \
  -e SMTP_USER=you@example.com \
  -e SMTP_PASS=your_password_or_app_token \
  --restart unless-stopped \
  ghcr.io/samcro1967/grylli
```
</details>

### Environment Variables

<details>
  <summary><strong>Show Environment Variables</strong></summary>

| Variable           | Description                                                        | Example/Notes                             |
|--------------------|--------------------------------------------------------------------|-------------------------------------------|
| `TZ`               | Timezone for the container                                         | `America/Chicago`                         |
| `PUID`             | User ID for container process (for volume permissions)             | `1000`                                    |
| `PGID`             | Group ID for container process                                     | `1000`                                    |
| `GRYLLI_DATA_DIR`  | Directory for persistent data inside the container                 | `/data`                                   |
| `DEBUG`            | Enable or disable debug mode                                       | `False` (use `True` for debugging)        |
| `FQDN`             | Public base URL of your Grylli instance                            | `http://your.domain.com:5069`             |
| `BASE_URL`         | Base URL path for Grylli (use `/grylli` or `/`)                    | `/grylli`                                 |
| `FLASK_APP_PORT`   | Port Grylli listens on inside the container                        | `5069`                                    |
| `FLASK_APP_KEY`    | Secret key for Flask session security                              | *(generate a secure random string)*       |
| `FERRET_KEY`       | Encryption key for sensitive data (Fernet, 32-byte base64 string)  | *(generate with Fernet)*                  |
| `SIGNUP_CODE`      | Registration code required for new sign-ups                        | `YourSuperSecretCode123!`                 |
| `DEFAULT_LANGUAGE` | Default language code                                              | `en`                                      |
| `SMTP_HOST`        | SMTP server hostname                                               | `smtp.example.com`                        |
| `SMTP_PORT`        | SMTP server port                                                   | `587` (for TLS), `465` (for SSL)          |
| `SMTP_USE_TLS`     | Use TLS for SMTP connection (1 for yes, 0 for no)                  | `1`                                       |
| `EMAIL_FROM`       | Default sender email address                                       | `you@example.com`                         |
| `SMTP_USER`        | SMTP authentication username                                       | `you@example.com`                         |
| `SMTP_PASS`        | SMTP authentication password or app token                          | `your_password_or_app_token`              |
</details>

> **Note:** See [`docker-compose.sample.yml`](./docker-compose.sample.yml) for instructions on how to generate your own `FLASK_APP_KEY` and `FERRET_KEY`.

## Credits & Key Dependencies

- [Flask](https://flask.palletsprojects.com/) — Python web framework
- [Flask-WTF](https://flask-wtf.readthedocs.io/) — Secure web forms with CSRF protection
- [Flask-Login](https://flask-login.readthedocs.io/) — User session and authentication management
- [Flask-Migrate](https://flask-migrate.readthedocs.io/) — Database migrations powered by Alembic
- [Flask-Babel](https://pythonhosted.org/Flask-Babel/) — Internationalization (i18n) and localization
- [email-validator](https://email-validator.readthedocs.io/) — Email address validation
- [cryptography](https://cryptography.io/) — Secure encryption for sensitive data
- [APScheduler](https://apscheduler.readthedocs.io/) — Advanced Python scheduling
- [Apprise](https://github.com/caronc/apprise) — Push notification and alert library
- [GPT-PO Translator](https://github.com/gaborvecsei/gpt-po-translator) — Automated PO file translation with GPT
- [gunicorn](https://gunicorn.org/) — Production Python WSGI server

Special thanks to these libraries and their authors for making Grylli possible!

---

## Recommended Third-Party Services

- [webhook (adnanh/webhook)](https://github.com/adnanh/webhook) — Simple webhook server

