// application.js
import { Application } from "https://cdn.jsdelivr.net/npm/@hotwired/stimulus@3.0.0/dist/stimulus.js";

import SidebarController from "./controllers/sidebar_controller.js";
import CollapseController from "./controllers/collapse_controller.js";
import ThemeController from "./controllers/theme_controller.js";
import LangController from "./controllers/lang_controller.js";
import RoleModalController from "./controllers/role_modal_controller.js";
import ListToggleController from "./controllers/list_toggle_controller.js";
import CollapsibleItemController from "./controllers/collapsible_item_controller.js";
import ConfirmController from "./controllers/confirm_controller.js";
import RevealPasswordController from "./controllers/reveal_password_controller.js";
import RedirectButtonController from "./controllers/redirect_button_controller.js";
import FlashMessageController from "./controllers/flash-message_controller.js";
import ProfileDropdownController from "./controllers/profile_dropdown_controller.js";
import UserFormController from "./controllers/user_form_controller.js";
import BootstrapFormController from "./controllers/bootstrap_form_controller.js";
import SignupFormController from "./controllers/signup_form_controller.js";
import ResetPasswordController from "./controllers/reset_password_controller.js";
import ForgotPasswordController from "./controllers/forgot_password_controller.js";
import ForgotUsernameController from "./controllers/forgot_username_controller.js";
import EmailStatusController from "./controllers/email_status_controller.js";
import AppriseListToggleController from "./controllers/apprise_list_toggle_controller.js";
import AppriseFormController from "./controllers/apprise_form_controller.js";
import AppriseValidateController from "./controllers/apprise_validate_controller.js";
import WebhookListToggleController from "./controllers/webhook_list_toggle_controller.js";
import WebhookFormController from "./controllers/webhook_form_controller.js";
import SmtpFormController from "./controllers/smtp_form_controller.js";
import RateLimitRedirectController from "./controllers/rate_limit_redirect_controller.js";
import RedirectController from "./controllers/redirect_controller.js";
import LayoutDebugController from "./controllers/layout_debug_controller.js";
import ToggleHelpController from "./controllers/toggle_help_controller.js";
import VersionCheckController from "./controllers/version_check_controller.js";
import InsecureWarningController from "./controllers/insecure_warning_controller.js"
import SidebarActiveController from "./controllers/sidebar_active_controller.js"
import TabsController from "./controllers/tabs_controller.js"
import ActionTitleController from "./controllers/action_title_controller.js";
import BackgroundController from "./controllers/background_controller.js";
import FontController from "./controllers/font_controller.js"
import FontSizeController from "./controllers/font_size_controller.js"
import RoundednessController from "./controllers/roundedness_controller.js";
import ContrastController from "./controllers/contrast_controller.js";
import TrackingController from "./controllers/tracking_controller.js";
import LineHeightController from "./controllers/line_height_controller.js";
import ProfileTitleController from "./controllers/profile_title_controller.js"

const application = Application.start();
application.register("sidebar", SidebarController);
application.register("collapse", CollapseController);
application.register("theme", ThemeController);
application.register("lang", LangController);
application.register("role-modal", RoleModalController);
application.register("list-toggle", ListToggleController);
application.register("collapsible-item", CollapsibleItemController);
application.register("confirm", ConfirmController);
application.register("reveal-password", RevealPasswordController);
application.register("redirect-button", RedirectButtonController);
application.register("flash-message", FlashMessageController);
application.register("profile-dropdown", ProfileDropdownController);
application.register("user-form", UserFormController);
application.register("bootstrap-form", BootstrapFormController);
application.register("signup-form", SignupFormController);
application.register("reset-password", ResetPasswordController);
application.register("forgot-password", ForgotPasswordController);
application.register("forgot-username", ForgotUsernameController);
application.register("email-status", EmailStatusController);
application.register("apprise-list-toggle", AppriseListToggleController);
application.register("apprise-form", AppriseFormController);
application.register("apprise-validate", AppriseValidateController);
application.register("webhook-list-toggle", WebhookListToggleController);
application.register("webhook-form", WebhookFormController);
application.register("smtp-form", SmtpFormController);
application.register("rate-limit-redirect", RateLimitRedirectController);
application.register("redirect", RedirectController);
application.register("layout-debug", LayoutDebugController);
application.register("toggle-help", ToggleHelpController);
application.register("version-check", VersionCheckController);
application.register("insecure-warning", InsecureWarningController)
application.register("sidebar-active", SidebarActiveController)
application.register("tabs", TabsController)
application.register("action-title", ActionTitleController);
application.register("background", BackgroundController);
application.register("font", FontController);
application.register("font-size", FontSizeController);
application.register("roundedness", RoundednessController);
application.register("contrast", ContrastController);
application.register("tracking", TrackingController);
application.register("line-height", LineHeightController);
application.register("profile-title", ProfileTitleController)

window.Stimulus = application;
