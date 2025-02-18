from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    REVIEW_NEEDED = "review_needed"
    READY_FOR_EXIT = "ready_for_exit"
    COMPLETED = "completed"

class FormStatus(str, Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"

class StakeholderRole(str, Enum):
    LEASE_EXIT_MANAGEMENT = "lease_exit_management"
    ADVISORY = "advisory"
    IFM = "ifm"
    LEGAL = "legal"
    MAC = "mac"
    PJM = "pjm"
    ACCOUNTING = "accounting"

class Document(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    name: str
    file_path: str
    document_type: str
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class FormData(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    form_type: str
    data: Dict[str, Any]
    status: FormStatus
    submitted_by: str
    submitted_at: Optional[datetime] = None
    last_updated_at: datetime = Field(default_factory=datetime.utcnow)
    documents: List[Document] = Field(default_factory=list)

class ApprovalStep(BaseModel):
    role: StakeholderRole
    status: str
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    comments: Optional[str] = None

class LeaseExit(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    lease_id: str
    property_details: Dict[str, Any]
    status: WorkflowStatus = WorkflowStatus.DRAFT
    current_step: str
    forms: Dict[str, FormData] = Field(default_factory=dict)
    approval_chain: List[ApprovalStep] = Field(default_factory=list)
    documents: List[Document] = Field(default_factory=list)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Notification(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    lease_exit_id: str
    recipient_role: StakeholderRole
    recipient_email: str
    subject: str
    message: str
    notification_type: str
    status: str = "pending"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    sent_at: Optional[datetime] = None

class User(BaseModel):
    id: str = Field(default_factory=lambda: str(ObjectId()))
    email: str
    full_name: str
    role: StakeholderRole
    hashed_password: str
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None