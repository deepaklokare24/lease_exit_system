"""
Celery tasks for the Lease Exit System.

This file defines Celery tasks that wrap around our task classes.
"""

import asyncio
from celery_app import celery_app
from tasks import notification_tasks, approval_tasks, form_tasks, workflow_tasks
from datetime import datetime, timedelta

# Helper function to run async functions in Celery tasks
def run_async(async_func, *args, **kwargs):
    """Run an async function from a synchronous context."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(async_func(*args, **kwargs))

# Notification Tasks
@celery_app.task(name="create_notification")
def create_notification(lease_exit_id, recipient_role, subject, message):
    """Create a notification."""
    return run_async(
        notification_tasks.execute_create_notification,
        lease_exit_id, recipient_role, subject, message
    )

@celery_app.task(name="notify_workflow_update")
def notify_workflow_update(lease_exit_id, update_type):
    """Notify stakeholders about a workflow update."""
    message = f"Workflow update: {update_type} for lease exit {lease_exit_id}"
    subject = f"Lease Exit {lease_exit_id} Update"
    return run_async(
        notification_tasks.execute_create_notification,
        lease_exit_id, "all", subject, message
    )

@celery_app.task(name="notify_multiple_roles")
def notify_multiple_roles(lease_exit_id, roles, subject, message):
    """Notify multiple roles about a lease exit."""
    results = []
    for role in roles:
        result = run_async(
            notification_tasks.execute_create_notification,
            lease_exit_id, role, subject, message
        )
        results.append(result)
    return results

@celery_app.task(name="resend_failed_notifications")
def resend_failed_notifications():
    """Resend failed notifications."""
    return run_async(
        notification_tasks.execute_resend_failed_notifications
    )

# Approval Tasks
@celery_app.task(name="create_approval_chain")
def create_approval_chain(lease_exit_id, required_approvers):
    """Create an approval chain."""
    return run_async(
        approval_tasks.execute_create_approval_chain,
        lease_exit_id, required_approvers
    )

@celery_app.task(name="process_approval")
def process_approval(lease_exit_id, approver_role, approved, comments=None):
    """Process an approval decision."""
    return run_async(
        approval_tasks.execute_process_approval,
        lease_exit_id, approver_role, approved, comments
    )

@celery_app.task(name="notify_approvers")
def notify_approvers(lease_exit_id, approver_roles):
    """Notify approvers about a pending approval."""
    return run_async(
        approval_tasks.notify_approvers,
        lease_exit_id, approver_roles
    )

# Form Tasks
@celery_app.task(name="create_form_template")
def create_form_template(form_type, required_fields, optional_fields=None):
    """Create a form template."""
    task = run_async(
        form_tasks.create_form_template_task,
        form_type, required_fields, optional_fields
    )
    return {"task_created": str(task)}

@celery_app.task(name="validate_form_submission")
def validate_form_submission(form_type, form_data):
    """Validate a form submission."""
    task = run_async(
        form_tasks.validate_form_submission_task,
        form_type, form_data
    )
    return {"task_created": str(task)}

# Workflow Tasks
@celery_app.task(name="create_workflow")
def create_workflow(workflow_type, requirements):
    """Create a workflow."""
    task = run_async(
        workflow_tasks.create_workflow_task,
        workflow_type, requirements
    )
    return {"task_created": str(task)}

@celery_app.task(name="update_workflow_status")
def update_workflow_status(lease_exit_id, status, comments=None):
    """Update a workflow status."""
    return run_async(
        workflow_tasks.execute_update_workflow_status,
        lease_exit_id, status, comments
    )

@celery_app.task(name="initiate_lease_exit")
def initiate_lease_exit(lease_exit_data):
    """Initiate a new lease exit."""
    return run_async(
        workflow_tasks.execute_initiate_lease_exit,
        lease_exit_data
    )

# Periodic Tasks
@celery_app.task(name="check_pending_approvals")
def check_pending_approvals():
    """Check for pending approvals and send reminders."""
    # Get all lease exits with pending approvals
    lease_exits_with_pending_approvals = run_async(
        workflow_tasks.get_lease_exits_with_pending_approvals
    )
    
    results = []
    for lease_exit in lease_exits_with_pending_approvals:
        # Check if approval is overdue (more than 3 days old)
        for approval in lease_exit.get('approval_chain', []):
            if approval.get('status') == 'pending':
                # Send reminder to the approver
                result = run_async(
                    notification_tasks.execute_create_notification,
                    lease_exit['id'],
                    approval['role'],
                    f"Reminder: Pending Approval for Lease Exit {lease_exit['id']}",
                    f"You have a pending approval for lease exit {lease_exit['id']} that requires your attention."
                )
                results.append(result)
    
    return {
        "status": "completed", 
        "message": f"Sent {len(results)} approval reminders", 
        "details": results
    }

@celery_app.task(name="check_workflow_deadlines")
def check_workflow_deadlines():
    """Check for approaching workflow deadlines and send notifications."""
    # Get all active lease exits
    active_lease_exits = run_async(
        workflow_tasks.get_active_lease_exits
    )
    
    results = []
    for lease_exit in active_lease_exits:
        # Check if the exit date is approaching (within 7 days)
        exit_date = lease_exit.get('exit_date')
        if exit_date:
            exit_date = datetime.fromisoformat(exit_date.replace('Z', '+00:00'))
            days_remaining = (exit_date - datetime.now()).days
            
            if 0 < days_remaining <= 7:
                # Send notification to all stakeholders
                result = run_async(
                    notification_tasks.execute_create_notification,
                    lease_exit['id'],
                    'all',
                    f"Approaching Deadline: Lease Exit {lease_exit['id']}",
                    f"The lease exit {lease_exit['id']} is scheduled to complete in {days_remaining} days."
                )
                results.append(result)
    
    return {
        "status": "completed", 
        "message": f"Sent {len(results)} deadline notifications", 
        "details": results
    }