# Import task classes to make them available
from tasks.notification_tasks import NotificationTasks
from tasks.approval_tasks import ApprovalTasks
from tasks.form_tasks import FormTasks
from tasks.workflow_tasks import WorkflowTasks

# Create instances for easy access
notification_tasks = NotificationTasks()
approval_tasks = ApprovalTasks()
form_tasks = FormTasks()
workflow_tasks = WorkflowTasks()
