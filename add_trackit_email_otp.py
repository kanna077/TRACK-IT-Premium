from pathlib import Path
import json
import re
import shutil
import textwrap
from datetime import datetime

PAYLOAD = json.loads('{"models": "from django.conf import settings\\nfrom django.contrib.auth.models import AbstractUser\\nfrom django.db import models\\n\\n\\nclass User(AbstractUser):\\n    class Role(models.TextChoices):\\n        STUDENT = \\"STUDENT\\", \\"Campus User / Student\\"\\n        FACULTY = \\"FACULTY\\", \\"Faculty / Authorized Staff\\"\\n        EXTERNAL_FINDER = \\"EXTERNAL_FINDER\\", \\"External Finder\\"\\n        ADMIN = \\"ADMIN\\", \\"Administrator\\"\\n\\n    email = models.EmailField(unique=True)\\n    role = models.CharField(\\n        max_length=20,\\n        choices=Role.choices,\\n        default=Role.STUDENT,\\n    )\\n    college_id = models.CharField(\\n        max_length=30,\\n        unique=True,\\n        null=True,\\n        blank=True,\\n    )\\n    department = models.CharField(max_length=100, blank=True)\\n    phone = models.CharField(max_length=15, blank=True)\\n    is_email_verified = models.BooleanField(default=False)\\n\\n    def __str__(self):\\n        return self.email or self.username\\n\\n\\nclass EmailVerificationOTP(models.Model):\\n    user = models.OneToOneField(\\n        settings.AUTH_USER_MODEL,\\n        on_delete=models.CASCADE,\\n        related_name=\\"email_verification_otp\\",\\n    )\\n    code = models.CharField(max_length=6)\\n    expires_at = models.DateTimeField()\\n    attempts = models.PositiveSmallIntegerField(default=0)\\n    updated_at = models.DateTimeField(auto_now=True)\\n\\n    def __str__(self):\\n        return f\\"Email verification for {self.user.email}\\"\\n", "views": "import secrets\\nfrom datetime import timedelta\\nfrom smtplib import SMTPException\\n\\nfrom django.conf import settings\\nfrom django.contrib.auth import authenticate\\nfrom django.core.mail import send_mail\\nfrom django.db import transaction\\nfrom django.utils import timezone\\nfrom rest_framework import status\\nfrom rest_framework.authtoken.models import Token\\nfrom rest_framework.permissions import AllowAny, IsAuthenticated\\nfrom rest_framework.response import Response\\nfrom rest_framework.views import APIView\\n\\nfrom .models import EmailVerificationOTP, User\\nfrom .serializers import RegisterSerializer, UserSerializer\\n\\n\\nOTP_VALID_MINUTES = 10\\nMAX_OTP_ATTEMPTS = 5\\n\\n\\ndef send_verification_otp(user):\\n    code = f\\"{secrets.randbelow(1_000_000):06d}\\"\\n\\n    EmailVerificationOTP.objects.update_or_create(\\n        user=user,\\n        defaults={\\n            \\"code\\": code,\\n            \\"expires_at\\": (\\n                timezone.now() + timedelta(minutes=OTP_VALID_MINUTES)\\n            ),\\n            \\"attempts\\": 0,\\n        },\\n    )\\n\\n    send_mail(\\n        subject=\\"TRACK-IT email verification OTP\\",\\n        message=(\\n            f\\"Hello {user.username},\\\\n\\\\n\\"\\n            f\\"Your TRACK-IT verification OTP is: {code}\\\\n\\\\n\\"\\n            f\\"This OTP expires in {OTP_VALID_MINUTES} minutes. \\"\\n            \\"Do not share it with anyone.\\"\\n        ),\\n        from_email=settings.DEFAULT_FROM_EMAIL,\\n        recipient_list=[user.email],\\n        fail_silently=False,\\n    )\\n\\n\\nclass RegisterView(APIView):\\n    permission_classes = [AllowAny]\\n    authentication_classes = []\\n\\n    def post(self, request):\\n        serializer = RegisterSerializer(data=request.data)\\n        serializer.is_valid(raise_exception=True)\\n        user = serializer.save()\\n\\n        try:\\n            send_verification_otp(user)\\n        except (SMTPException, OSError):\\n            user.delete()\\n            return Response(\\n                {\\n                    \\"detail\\": (\\n                        \\"Registration email could not be sent. \\"\\n                        \\"Check the TRACK-IT email configuration.\\"\\n                    )\\n                },\\n                status=status.HTTP_503_SERVICE_UNAVAILABLE,\\n            )\\n\\n        return Response(\\n            {\\n                \\"message\\": (\\n                    \\"Registration successful. A 6-digit OTP was sent \\"\\n                    \\"to your registered email address.\\"\\n                ),\\n                \\"email\\": user.email,\\n            },\\n            status=status.HTTP_201_CREATED,\\n        )\\n\\n\\nclass VerifyEmailOTPView(APIView):\\n    permission_classes = [AllowAny]\\n    authentication_classes = []\\n\\n    def post(self, request):\\n        email = str(request.data.get(\\"email\\", \\"\\")).strip().lower()\\n        otp = str(request.data.get(\\"otp\\", \\"\\")).strip()\\n\\n        if not email or not otp:\\n            return Response(\\n                {\\"detail\\": \\"Email and OTP are required.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        try:\\n            user = User.objects.get(email__iexact=email)\\n        except User.DoesNotExist:\\n            return Response(\\n                {\\"detail\\": \\"No registration was found for this email.\\"},\\n                status=status.HTTP_404_NOT_FOUND,\\n            )\\n\\n        if user.is_email_verified:\\n            return Response(\\n                {\\"message\\": \\"Email is already verified. You may log in.\\"}\\n            )\\n\\n        try:\\n            record = EmailVerificationOTP.objects.get(user=user)\\n        except EmailVerificationOTP.DoesNotExist:\\n            return Response(\\n                {\\"detail\\": \\"No active OTP exists. Request a new OTP.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        if timezone.now() >= record.expires_at:\\n            record.delete()\\n            return Response(\\n                {\\"detail\\": \\"OTP expired. Request a new OTP.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        if record.attempts >= MAX_OTP_ATTEMPTS:\\n            return Response(\\n                {\\n                    \\"detail\\": (\\n                        \\"Too many incorrect attempts. Request a new OTP.\\"\\n                    )\\n                },\\n                status=status.HTTP_429_TOO_MANY_REQUESTS,\\n            )\\n\\n        if not secrets.compare_digest(record.code, otp):\\n            record.attempts += 1\\n            record.save(update_fields=[\\"attempts\\", \\"updated_at\\"])\\n            return Response(\\n                {\\"detail\\": \\"Incorrect OTP.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        with transaction.atomic():\\n            user.is_email_verified = True\\n            user.save(update_fields=[\\"is_email_verified\\"])\\n            record.delete()\\n\\n        return Response(\\n            {\\"message\\": \\"Email verified successfully. You can now log in.\\"}\\n        )\\n\\n\\nclass ResendEmailOTPView(APIView):\\n    permission_classes = [AllowAny]\\n    authentication_classes = []\\n\\n    def post(self, request):\\n        email = str(request.data.get(\\"email\\", \\"\\")).strip().lower()\\n\\n        if not email:\\n            return Response(\\n                {\\"detail\\": \\"Email is required.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        try:\\n            user = User.objects.get(email__iexact=email)\\n        except User.DoesNotExist:\\n            return Response(\\n                {\\"detail\\": \\"No registration was found for this email.\\"},\\n                status=status.HTTP_404_NOT_FOUND,\\n            )\\n\\n        if user.is_email_verified:\\n            return Response(\\n                {\\"message\\": \\"Email is already verified. You may log in.\\"}\\n            )\\n\\n        try:\\n            send_verification_otp(user)\\n        except (SMTPException, OSError):\\n            return Response(\\n                {\\"detail\\": \\"OTP email could not be sent.\\"},\\n                status=status.HTTP_503_SERVICE_UNAVAILABLE,\\n            )\\n\\n        return Response(\\n            {\\"message\\": \\"A new OTP was sent to your registered email.\\"}\\n        )\\n\\n\\nclass LoginView(APIView):\\n    permission_classes = [AllowAny]\\n    authentication_classes = []\\n\\n    def post(self, request):\\n        identifier = str(request.data.get(\\"identifier\\", \\"\\")).strip()\\n        password = request.data.get(\\"password\\", \\"\\")\\n\\n        if not identifier or not password:\\n            return Response(\\n                {\\"detail\\": \\"Username/email and password are required.\\"},\\n                status=status.HTTP_400_BAD_REQUEST,\\n            )\\n\\n        username = identifier\\n        if \\"@\\" in identifier:\\n            try:\\n                username = User.objects.get(\\n                    email__iexact=identifier\\n                ).username\\n            except User.DoesNotExist:\\n                pass\\n\\n        user = authenticate(\\n            request=request,\\n            username=username,\\n            password=password,\\n        )\\n\\n        if user is None:\\n            return Response(\\n                {\\"detail\\": \\"Invalid username/email or password.\\"},\\n                status=status.HTTP_401_UNAUTHORIZED,\\n            )\\n\\n        if not user.is_email_verified and not user.is_superuser:\\n            return Response(\\n                {\\n                    \\"detail\\": (\\n                        \\"Email is not verified. Enter the OTP sent \\"\\n                        \\"during registration.\\"\\n                    )\\n                },\\n                status=status.HTTP_403_FORBIDDEN,\\n            )\\n\\n        Token.objects.filter(user=user).delete()\\n        token = Token.objects.create(user=user)\\n\\n        return Response(\\n            {\\n                \\"token\\": token.key,\\n                \\"user\\": UserSerializer(user).data,\\n            }\\n        )\\n\\n\\nclass CurrentUserView(APIView):\\n    permission_classes = [IsAuthenticated]\\n\\n    def get(self, request):\\n        return Response(UserSerializer(request.user).data)\\n\\n\\nclass LogoutView(APIView):\\n    permission_classes = [IsAuthenticated]\\n\\n    def post(self, request):\\n        Token.objects.filter(user=request.user).delete()\\n        return Response({\\"message\\": \\"Logged out successfully.\\"})\\n", "urls": "from django.urls import path\\n\\nfrom .views import (\\n    CurrentUserView,\\n    LoginView,\\n    LogoutView,\\n    RegisterView,\\n    ResendEmailOTPView,\\n    VerifyEmailOTPView,\\n)\\n\\n\\nurlpatterns = [\\n    path(\\"register/\\", RegisterView.as_view()),\\n    path(\\"verify-email/\\", VerifyEmailOTPView.as_view()),\\n    path(\\"resend-otp/\\", ResendEmailOTPView.as_view()),\\n    path(\\"login/\\", LoginView.as_view()),\\n    path(\\"logout/\\", LogoutView.as_view()),\\n    path(\\"me/\\", CurrentUserView.as_view()),\\n]\\n", "admin": "from django.contrib import admin\\nfrom django.contrib.auth.admin import UserAdmin\\n\\nfrom .models import EmailVerificationOTP, User\\n\\n\\n@admin.register(User)\\nclass CustomUserAdmin(UserAdmin):\\n    list_display = (\\n        \\"username\\",\\n        \\"email\\",\\n        \\"role\\",\\n        \\"is_email_verified\\",\\n        \\"is_staff\\",\\n        \\"is_active\\",\\n    )\\n    list_filter = (\\n        \\"role\\",\\n        \\"is_email_verified\\",\\n        \\"is_staff\\",\\n        \\"is_active\\",\\n    )\\n    fieldsets = UserAdmin.fieldsets + (\\n        (\\n            \\"TRACK-IT Information\\",\\n            {\\n                \\"fields\\": (\\n                    \\"role\\",\\n                    \\"college_id\\",\\n                    \\"department\\",\\n                    \\"phone\\",\\n                    \\"is_email_verified\\",\\n                )\\n            },\\n        ),\\n    )\\n    add_fieldsets = UserAdmin.add_fieldsets + (\\n        (\\n            \\"TRACK-IT Information\\",\\n            {\\n                \\"fields\\": (\\n                    \\"email\\",\\n                    \\"role\\",\\n                    \\"college_id\\",\\n                    \\"department\\",\\n                    \\"phone\\",\\n                    \\"is_email_verified\\",\\n                )\\n            },\\n        ),\\n    )\\n\\n\\n@admin.register(EmailVerificationOTP)\\nclass EmailVerificationOTPAdmin(admin.ModelAdmin):\\n    list_display = (\\"user\\", \\"expires_at\\", \\"attempts\\", \\"updated_at\\")\\n    readonly_fields = (\\"code\\", \\"expires_at\\", \\"attempts\\", \\"updated_at\\")\\n    search_fields = (\\"user__email\\", \\"user__username\\")\\n", "new_functions": "  async function register(event: FormEvent<HTMLFormElement>) {\\n    event.preventDefault();\\n    const data = new FormData(event.currentTarget);\\n    const email = String(data.get(\\"email\\") ?? \\"\\").trim();\\n\\n    try {\\n      const response = await api.post(\\"/auth/register/\\", {\\n        username: data.get(\\"username\\"),\\n        email,\\n        password: data.get(\\"password\\"),\\n        password_confirm: data.get(\\"password\\"),\\n        role: data.get(\\"role\\"),\\n        college_id: data.get(\\"college_id\\"),\\n      });\\n\\n      setVerificationEmail(email);\\n      setVerificationOtp(\\"\\");\\n      setShowOtpForm(true);\\n      setMessage(response.data.message);\\n    } catch (error) {\\n      setMessage(errorMessage(error));\\n    }\\n  }\\n\\n  async function verifyRegistrationOtp(\\n    event: FormEvent<HTMLFormElement>\\n  ) {\\n    event.preventDefault();\\n\\n    try {\\n      const response = await api.post(\\"/auth/verify-email/\\", {\\n        email: verificationEmail,\\n        otp: verificationOtp,\\n      });\\n\\n      setShowOtpForm(false);\\n      setVerificationOtp(\\"\\");\\n      setMessage(response.data.message);\\n    } catch (error) {\\n      setMessage(errorMessage(error));\\n    }\\n  }\\n\\n  async function resendVerificationOtp() {\\n    try {\\n      const response = await api.post(\\"/auth/resend-otp/\\", {\\n        email: verificationEmail,\\n      });\\n      setMessage(response.data.message);\\n    } catch (error) {\\n      setMessage(errorMessage(error));\\n    }\\n  }\\n\\n  async function logout", "new_form": "          {!showOtpForm ? (\\n            <form className=\\"panel\\" onSubmit={register}>\\n              <h3>Register</h3>\\n              <input name=\\"username\\" placeholder=\\"Username\\" required />\\n              <input\\n                name=\\"email\\"\\n                type=\\"email\\"\\n                placeholder=\\"College email\\"\\n                required\\n              />\\n              <input name=\\"college_id\\" placeholder=\\"College ID\\" />\\n              <select name=\\"role\\" defaultValue=\\"STUDENT\\">\\n                <option value=\\"STUDENT\\">Campus User / Student</option>\\n                <option value=\\"EXTERNAL_FINDER\\">External Finder</option>\\n              </select>\\n              <input\\n                name=\\"password\\"\\n                type=\\"password\\"\\n                placeholder=\\"Strong password\\"\\n                required\\n              />\\n              <button type=\\"submit\\">Create account</button>\\n            </form>\\n          ) : (\\n            <form className=\\"panel\\" onSubmit={verifyRegistrationOtp}>\\n              <h3>Verify Email</h3>\\n              <p className=\\"muted\\">\\n                Enter the 6-digit OTP sent to {verificationEmail}\\n              </p>\\n              <input\\n                type=\\"text\\"\\n                inputMode=\\"numeric\\"\\n                maxLength={6}\\n                value={verificationOtp}\\n                onChange={(event) =>\\n                  setVerificationOtp(\\n                    event.target.value.replace(/\\\\D/g, \\"\\")\\n                  )\\n                }\\n                placeholder=\\"6-digit OTP\\"\\n                required\\n              />\\n              <button type=\\"submit\\">Verify email</button>\\n              <button\\n                type=\\"button\\"\\n                onClick={resendVerificationOtp}\\n              >\\n                Resend OTP\\n              </button>\\n              <button\\n                type=\\"button\\"\\n                onClick={() => setShowOtpForm(false)}\\n              >\\n                Back to registration\\n              </button>\\n            </form>\\n          )}"}')

ROOT = Path.cwd()
if not (ROOT / "backend" / "manage.py").exists():
    ROOT = Path(r"D:\track-it")

if not (ROOT / "backend" / "manage.py").exists():
    raise SystemExit("Run this script from D:\\track-it.")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
backup_root = ROOT / f"otp_backup_{timestamp}"

def backup(path):
    if path.exists():
        destination = backup_root / path.relative_to(ROOT)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, destination)

def replace_file(relative, content):
    path = ROOT / relative
    backup(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

replace_file("backend/apps/accounts/models.py", PAYLOAD["models"])
replace_file("backend/apps/accounts/views.py", PAYLOAD["views"])
replace_file("backend/apps/accounts/urls.py", PAYLOAD["urls"])
replace_file("backend/apps/accounts/admin.py", PAYLOAD["admin"])

settings_path = ROOT / "backend/config/settings.py"
backup(settings_path)
settings_text = settings_path.read_text(encoding="utf-8")
marker = "# TRACK-IT EMAIL OTP SETTINGS"
if marker not in settings_text:
    settings_text += textwrap.dedent("""

    # TRACK-IT EMAIL OTP SETTINGS
    EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
    EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
    EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
    EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
    EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
    EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
    DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", EMAIL_HOST_USER)
    EMAIL_TIMEOUT = 20
    """)
    settings_path.write_text(settings_text, encoding="utf-8")

page_path = ROOT / "frontend/src/app/page.tsx"
backup(page_path)
page = page_path.read_text(encoding="utf-8")

state_marker = '  const [message, setMessage] = useState("");'
if "verificationEmail" not in page:
    page = page.replace(
        state_marker,
        state_marker
        + '\n  const [verificationEmail, setVerificationEmail] = useState("");'
        + '\n  const [verificationOtp, setVerificationOtp] = useState("");'
        + '\n  const [showOtpForm, setShowOtpForm] = useState(false);',
        1,
    )

function_pattern = re.compile(
    r'  async function register\(event: FormEvent<HTMLFormElement>\) \{'
    r'.*?'
    r'\n  \}\n\n  async function logout',
    re.DOTALL,
)
if not function_pattern.search(page):
    raise SystemExit("Registration function not found in page.tsx.")
page = function_pattern.sub(
    lambda match: PAYLOAD["new_functions"],
    page,
    count=1,
)

form_pattern = re.compile(
    r'          <form className="panel" onSubmit=\{register\}>'
    r'.*?'
    r'          </form>',
    re.DOTALL,
)
if not form_pattern.search(page):
    raise SystemExit("Registration form not found in page.tsx.")
page = form_pattern.sub(
    lambda match: PAYLOAD["new_form"],
    page,
    count=1,
)
page_path.write_text(page, encoding="utf-8")

print("TRACK-IT email OTP feature applied successfully.")
print("Backup folder:", backup_root)
print("Now configure .env and run migrations.")
