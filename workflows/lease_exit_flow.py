from typing import Dict, Any, List
from crewai import Agent, Task, Flow
from crewai.flow import listen, start, router
from database.models import LeaseExit, FormStatus, WorkflowStatus, StakeholderRole
from utils.tools import DatabaseTool, NotificationTool, FormValidationTool
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
import yaml
import os

class LeaseExitFlow(Flow):
    def __init__(self):
        super().__init__()
        self.load_agent_configs()
        self.setup_tools()
        self.initialize_agents()

    def load_agent_configs(self):
        config_path = os.path.join(os.path.dirname(__file__), '../config/agents.yaml')
        with open(config_path, 'r') as file:
            self.agent_configs = yaml.safe_load(file)

    def setup_tools(self):
        self.db_tool = DatabaseTool()
        self.notification_tool = NotificationTool()
        self.form_tool = FormValidationTool()
        self.search_tool = SerperDevTool()
        self.scrape_tool = ScrapeWebsiteTool()

    def initialize_agents(self):
        self.workflow_specialist = Agent(
            **self.agent_configs['workflow_design_specialist'],
            tools=[self.db_tool, self.search_tool]
        )
        
        self.form_expert = Agent(
            **self.agent_configs['form_creation_expert'],
            tools=[self.form_tool, self.db_tool, self.scrape_tool]
        )
        
        self.approval_architect = Agent(
            **self.agent_configs['approval_process_architect'],
            tools=[self.db_tool, self.notification_tool]
        )

    @start()
    def initiate_lease_exit(self, lease_exit_data: Dict[str, Any]):
        """Initial form submission by Lease Exit Management Team"""
        task = Task(
            description=f"Create and validate initial lease exit form",
            agent=self.form_expert,
            context={
                "lease_data": lease_exit_data,
                "required_fields": [
                    "lease_id",
                    "property_address",
                    "exit_date",
                    "reason_for_exit"
                ]
            }
        )
        return task.execute()

    @listen(initiate_lease_exit)
    def notify_stakeholders(self, form_data):
        """Send notifications to Advisory, IFM, Legal"""
        task = Task(
            description="Send notifications to initial stakeholders",
            agent=self.approval_architect,
            context={
                "form_data": form_data,
                "recipients": [
                    StakeholderRole.ADVISORY,
                    StakeholderRole.IFM,
                    StakeholderRole.LEGAL
                ]
            }
        )
        return task.execute()

    @router(notify_stakeholders, paths=['advisory', 'ifm', 'legal'])
    def route_to_department(self, notification_status):
        """Route to appropriate department based on role"""
        return notification_status.recipient_role.lower()

    @listen('advisory')
    def process_advisory_review(self, context):
        """Handle Advisory department review"""
        task = Task(
            description="Process Advisory department review and requirements",
            agent=self.form_expert,
            context={
                "form_type": "advisory_review",
                "previous_data": context
            }
        )
        return task.execute()

    @listen('ifm')
    def process_ifm_review(self, context):
        """Handle IFM department review"""
        task = Task(
            description="Process IFM department review and scope",
            agent=self.form_expert,
            context={
                "form_type": "ifm_review",
                "previous_data": context
            }
        )
        return task.execute()

    @listen('legal')
    def process_legal_review(self, context):
        """Handle Legal department review"""
        task = Task(
            description="Process Legal department review and requirements",
            agent=self.form_expert,
            context={
                "form_type": "legal_review",
                "previous_data": context
            }
        )
        return task.execute()

    @listen(process_advisory_review)
    def notify_next_stakeholders(self, review_data):
        """Notify next stakeholders after Advisory review"""
        task = Task(
            description="Notify next stakeholders in the workflow",
            agent=self.approval_architect,
            context={
                "review_data": review_data,
                "recipients": [
                    StakeholderRole.LEGAL,
                    StakeholderRole.IFM,
                    StakeholderRole.ACCOUNTING
                ]
            }
        )
        return task.execute()

    @listen(process_ifm_review)
    def notify_mac(self, review_data):
        """Notify MAC after IFM review"""
        task = Task(
            description="Notify MAC for review",
            agent=self.approval_architect,
            context={
                "review_data": review_data,
                "recipients": [StakeholderRole.MAC]
            }
        )
        return task.execute()

    @listen(notify_mac)
    def process_mac_review(self, context):
        """Handle MAC review"""
        task = Task(
            description="Process MAC review and requirements",
            agent=self.form_expert,
            context={
                "form_type": "mac_review",
                "previous_data": context
            }
        )
        return task.execute()

    @listen(process_mac_review)
    def notify_pjm(self, review_data):
        """Notify PJM after MAC review"""
        task = Task(
            description="Notify PJM for review",
            agent=self.approval_architect,
            context={
                "review_data": review_data,
                "recipients": [StakeholderRole.PJM]
            }
        )
        return task.execute()

    @listen(notify_pjm)
    def process_pjm_review(self, context):
        """Handle PJM review"""
        task = Task(
            description="Process PJM review and requirements",
            agent=self.form_expert,
            context={
                "form_type": "pjm_review",
                "previous_data": context
            }
        )
        return task.execute()

    @listen(process_pjm_review)
    def notify_management_team(self, review_data):
        """Notify Lease Exit Management Team for final review"""
        task = Task(
            description="Notify management team for final review",
            agent=self.approval_architect,
            context={
                "review_data": review_data,
                "recipients": [StakeholderRole.LEASE_EXIT_MANAGEMENT]
            }
        )
        return task.execute()

    @listen(notify_management_team)
    def trigger_approval_process(self, context):
        """Trigger final approval process"""
        task = Task(
            description="Initiate final approval process",
            agent=self.approval_architect,
            context={
                "workflow_data": context,
                "required_approvers": [
                    StakeholderRole.ADVISORY,
                    StakeholderRole.IFM,
                    StakeholderRole.LEGAL,
                    StakeholderRole.LEASE_EXIT_MANAGEMENT
                ]
            }
        )
        return task.execute()

    @router(trigger_approval_process, paths=['approved', 'rejected'])
    def handle_approval_decision(self, approval_result):
        """Route based on approval decision"""
        if approval_result.get('status') == 'approved':
            return 'approved'
        return 'rejected'

    @listen('approved')
    def finalize_lease_exit(self, approval_data):
        """Handle approved lease exit"""
        task = Task(
            description="Finalize approved lease exit",
            agent=self.workflow_specialist,
            context={
                "approval_data": approval_data,
                "status": WorkflowStatus.READY_FOR_EXIT
            }
        )
        return task.execute()

    @listen('rejected')
    def handle_rejection(self, approval_data):
        """Handle rejected lease exit"""
        task = Task(
            description="Process lease exit rejection",
            agent=self.workflow_specialist,
            context={
                "approval_data": approval_data,
                "status": WorkflowStatus.REVIEW_NEEDED
            }
        )
        return task.execute()