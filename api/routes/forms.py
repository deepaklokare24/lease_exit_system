from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from typing import Dict, Any, List
from database.models import FormData, Document, StakeholderRole, FormStatus
from utils.tools import DatabaseTool, FormValidationTool
from pydantic import BaseModel
import os
from datetime import datetime
from database.connection import Database
from bson import ObjectId

router = APIRouter()
db_tool = DatabaseTool()
form_tool = FormValidationTool()

class FormTemplate(BaseModel):
    form_type: str
    fields: List[Dict[str, Any]]
    required_role: StakeholderRole

class FormTemplateResponse(FormTemplate):
    id: str
    created_at: str
    updated_at: str

class DocumentUploadResponse(BaseModel):
    id: str
    name: str
    file_path: str
    document_type: str
    uploaded_by: str
    uploaded_at: str

@router.post("/templates", response_model=FormTemplateResponse)
async def create_form_template(template: FormTemplate):
    """Create a new form template"""
    template_data = template.dict()
    template_data.update({
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    result = await db.form_templates.insert_one(template_data)
    template_data["id"] = str(result.inserted_id)
    
    return FormTemplateResponse(**template_data)

@router.get("/templates", response_model=List[FormTemplateResponse])
async def list_form_templates():
    """List all form templates"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    cursor = db.form_templates.find()
    templates = []
    async for doc in cursor:
        doc["id"] = str(doc["_id"])
        templates.append(FormTemplateResponse(**doc))
    return templates

@router.get("/templates/{template_id}", response_model=FormTemplateResponse)
async def get_form_template(template_id: str):
    """Get a specific form template"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    template = await db.form_templates.find_one({"_id": ObjectId(template_id)})
    if not template:
        raise HTTPException(status_code=404, detail="Form template not found")
    
    template["id"] = str(template["_id"])
    return FormTemplateResponse(**template)

@router.post("/{lease_exit_id}/documents", response_model=DocumentUploadResponse)
async def upload_document(
    lease_exit_id: str,
    document_type: str,
    file: UploadFile = File(...),
    uploaded_by: str = None
):
    """Upload a document for a form"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    
    # Ensure the lease exit exists
    doc = await db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    doc["id"] = str(doc.pop("_id"))
    lease_exit = LeaseExit(**doc)
    
    # Create documents directory if it doesn't exist
    upload_dir = f"uploads/{lease_exit_id}"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save the file
    file_path = f"{upload_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    # Create document record
    document = Document(
        name=file.filename,
        file_path=file_path,
        document_type=document_type,
        uploaded_by=uploaded_by,
        uploaded_at=datetime.utcnow().isoformat()
    )
    
    # Add document to lease exit
    if not lease_exit.documents:
        lease_exit.documents = []
    lease_exit.documents.append(document)
    
    # Update the lease exit in the database
    await db.lease_exits.update_one(
        {"_id": ObjectId(lease_exit_id)},
        {"$set": {"documents": [doc.dict() for doc in lease_exit.documents]}}
    )
    
    return DocumentUploadResponse(**document.dict())

@router.get("/{lease_exit_id}/documents", response_model=List[DocumentUploadResponse])
async def list_documents(lease_exit_id: str):
    """List all documents for a lease exit"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    
    # Ensure the lease exit exists
    doc = await db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    doc["id"] = str(doc.pop("_id"))
    lease_exit = LeaseExit(**doc)
    
    return [DocumentUploadResponse(**doc.dict()) for doc in lease_exit.documents]

@router.get("/{lease_exit_id}", response_model=List[FormData])
async def list_forms(lease_exit_id: str):
    """List all forms for a lease exit"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    
    # Ensure the lease exit exists
    doc = await db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    doc["id"] = str(doc.pop("_id"))
    lease_exit = LeaseExit(**doc)
    
    return list(lease_exit.forms.values())

@router.get("/{lease_exit_id}/{form_type}", response_model=FormData)
async def get_form(lease_exit_id: str, form_type: str):
    """Get a specific form for a lease exit"""
    # Get database instance from the Database class
    db = Database.client[Database.db_name]
    
    # Ensure the lease exit exists
    doc = await db.lease_exits.find_one({"_id": ObjectId(lease_exit_id)})
    if not doc:
        raise HTTPException(status_code=404, detail="Lease exit not found")
    
    doc["id"] = str(doc.pop("_id"))
    lease_exit = LeaseExit(**doc)
    
    form = lease_exit.forms.get(form_type)
    if not form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    return form
