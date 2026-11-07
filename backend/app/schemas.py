from datetime import datetime

from pydantic import AliasChoices, BaseModel, EmailStr, Field, field_validator, model_validator


class RegisterRequest(BaseModel):
    email: EmailStr
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        validation_alias=AliasChoices("display_name", "username"),
    )
    username: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        validation_alias=AliasChoices("username", "display_name"),
    )
    password: str = Field(min_length=8, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=128)

    @field_validator("display_name", "username")
    @classmethod
    def _normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Display name cannot be blank.")
        if len(trimmed) < 2:
            raise ValueError("Display name must be at least 2 characters long.")
        return trimmed

    @model_validator(mode="after")
    def _validate_name_and_password(self) -> "RegisterRequest":
        chosen_name = self.display_name or self.username
        if not chosen_name:
            raise ValueError("Display name is required.")
        self.display_name = chosen_name
        self.username = chosen_name
        if self.confirm_password is not None and self.confirm_password != self.password:
            raise ValueError("Passwords do not match.")
        return self


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr
    recovery_code: str = Field(min_length=8, max_length=40)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def _validate_password_match(self) -> "ForgotPasswordRequest":
        if self.confirm_password is not None and self.confirm_password != self.new_password:
            raise ValueError("Passwords do not match.")
        return self


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)
    confirm_password: str | None = Field(default=None, min_length=8, max_length=128)

    @model_validator(mode="after")
    def _validate_password_match(self) -> "ChangePasswordRequest":
        if self.confirm_password is not None and self.confirm_password != self.new_password:
            raise ValueError("Passwords do not match.")
        return self


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        validation_alias=AliasChoices("display_name", "username"),
    )
    username: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        validation_alias=AliasChoices("username", "display_name"),
    )

    @field_validator("display_name", "username")
    @classmethod
    def _normalize_display_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if not trimmed:
            raise ValueError("Display name cannot be blank.")
        if len(trimmed) < 2:
            raise ValueError("Display name must be at least 2 characters long.")
        return trimmed

    @model_validator(mode="after")
    def _validate_name(self) -> "ProfileUpdateRequest":
        chosen_name = self.display_name or self.username
        if not chosen_name:
            raise ValueError("Display name is required.")
        self.display_name = chosen_name
        self.username = chosen_name
        return self


class UserPublic(BaseModel):
    id: int
    email: EmailStr
    display_name: str
    username: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    user: UserPublic
    recovery_code: str | None = None


class ActivityLogPublic(BaseModel):
    id: int
    action: str
    detail: str
    created_at: datetime

    model_config = {"from_attributes": True}


class SystemStatus(BaseModel):
    product: str = "OBITO AI"
    owner: str = "FAKHIR AI"
    tagline: str = "Your Voice. Your Commands. Your Intelligence."
    phase: int = 2
    obito_status: str
    active_model: str
    voice_status: str
    pc_connection: str
    roblox_connection: str
    active_tasks: list[str]
    notes: list[str]


class ChatConversationPublic(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessagePublic(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageRequest(BaseModel):
    conversation_id: int | None = Field(default=None, gt=0)
    content: str = Field(min_length=1, max_length=4000)


class ChatTurnPublic(BaseModel):
    conversation: ChatConversationPublic
    messages: list[ChatMessagePublic]


class ChatModelStatus(BaseModel):
    provider: str
    model: str
    configured: bool


class ProjectCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)
    project_type: str = Field(default="general", min_length=1, max_length=50)


class ProjectUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    description: str | None = Field(default=None, max_length=2000)
    project_type: str | None = Field(default=None, min_length=1, max_length=50)


class ProjectPublic(BaseModel):
    id: int
    user_id: int
    name: str
    description: str
    project_type: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MemoryEntryCreateRequest(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    content: str = Field(default="", max_length=4000)
    category: str = Field(default="general", min_length=1, max_length=50)


class MemoryEntryUpdateRequest(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=120)
    content: str | None = Field(default=None, max_length=4000)
    category: str | None = Field(default=None, min_length=1, max_length=50)


class MemoryEntryPublic(BaseModel):
    id: int
    user_id: int
    title: str
    content: str
    category: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
