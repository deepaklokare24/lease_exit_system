from typing import Dict, Any, List, Optional, Tuple
from crew.agent import Agent
from database.models import Workflow, WorkflowStep, LeaseExit, StakeholderRole
from tools.workflow_tool import WorkflowTool
from tools.database_tool import DatabaseTool

class WorkflowDesignerAgent(Agent):
    """
    An AI agent responsible for designing and optimizing workflows within the Lease Exit System.
    This agent analyzes lease exit context and creates appropriate workflow steps and transitions.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the Workflow Designer Agent.
        
        Args:
            config: Agent configuration parameters
        """
        super().__init__(config)
        self.name = "Workflow Designer Agent"
        self.description = "Designs and optimizes lease exit workflows"
        self.workflow_tool = WorkflowTool()
        self.db_tool = DatabaseTool()
    
    async def create_standard_workflow(self, lease_type: str, property_details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a standard workflow for a lease exit based on lease type and property details.
        
        Args:
            lease_type: The type of lease (commercial, residential, etc.)
            property_details: Details about the property
            
        Returns:
            Workflow definition and metadata
        """
        # Analyze inputs to determine workflow requirements
        steps = self._determine_workflow_steps(lease_type, property_details)
        transitions = self._determine_workflow_transitions(steps)
        
        # Create workflow structure
        workflow = {
            "name": f"{lease_type} Lease Exit Workflow",
            "description": f"Standard workflow for exiting a {lease_type} lease",
            "steps": steps,
            "transitions": transitions,
            "lease_type": lease_type,
            "metadata": {
                "property_type": property_details.get("property_type", "unknown"),
                "estimated_duration_days": self._estimate_workflow_duration(steps),
                "requires_legal_review": self._requires_legal_review(lease_type, property_details)
            }
        }
        
        # Save the workflow to database
        workflow_id = await self.workflow_tool.save_workflow(workflow)
        workflow["id"] = workflow_id
        
        return workflow
    
    async def customize_workflow(self, workflow_id: str, customizations: Dict[str, Any]) -> Dict[str, Any]:
        """
        Customize an existing workflow based on specific requirements.
        
        Args:
            workflow_id: The ID of the base workflow
            customizations: Customization parameters
            
        Returns:
            Customized workflow definition
        """
        # Retrieve the base workflow
        base_workflow = await self.workflow_tool.get_workflow(workflow_id)
        if not base_workflow:
            raise ValueError(f"Workflow with ID {workflow_id} not found")
        
        # Apply customizations
        customized_workflow = self._apply_workflow_customizations(base_workflow, customizations)
        
        # Save as a new workflow
        new_workflow_id = await self.workflow_tool.save_workflow(customized_workflow)
        customized_workflow["id"] = new_workflow_id
        
        return customized_workflow
    
    async def analyze_workflow_performance(self, workflow_id: str) -> Dict[str, Any]:
        """
        Analyze the performance of an existing workflow.
        
        Args:
            workflow_id: The ID of the workflow to analyze
            
        Returns:
            Performance metrics and suggestions for improvement
        """
        # Get workflow details
        workflow = await self.workflow_tool.get_workflow(workflow_id)
        if not workflow:
            raise ValueError(f"Workflow with ID {workflow_id} not found")
        
        # Get all lease exits using this workflow
        lease_exits = await self.db_tool.find_documents(
            "lease_exits", 
            {"workflow_id": workflow_id}
        )
        
        # Analyze performance
        performance_metrics = self._calculate_performance_metrics(workflow, lease_exits)
        bottlenecks = self._identify_bottlenecks(workflow, lease_exits)
        suggestions = self._generate_improvement_suggestions(bottlenecks, performance_metrics)
        
        return {
            "workflow_id": workflow_id,
            "workflow_name": workflow.get("name", ""),
            "metrics": performance_metrics,
            "bottlenecks": bottlenecks,
            "suggestions": suggestions
        }
    
    async def generate_workflow_for_lease_exit(self, lease_exit_id: str) -> Dict[str, Any]:
        """
        Generate a customized workflow for a specific lease exit.
        
        Args:
            lease_exit_id: The ID of the lease exit
            
        Returns:
            Generated workflow
        """
        # Get lease exit details
        lease_exit = await self.db_tool.get_document("lease_exits", lease_exit_id)
        if not lease_exit:
            raise ValueError(f"Lease exit with ID {lease_exit_id} not found")
        
        # Extract lease type and property details
        lease_type = lease_exit.get("lease_type", "standard")
        property_details = lease_exit.get("property_details", {})
        
        # Create base workflow
        base_workflow = await self.create_standard_workflow(lease_type, property_details)
        
        # Apply customizations based on specific lease exit details
        customizations = self._derive_customizations_from_lease_exit(lease_exit)
        
        # Customize workflow if needed
        if customizations:
            workflow = await self.customize_workflow(base_workflow["id"], customizations)
        else:
            workflow = base_workflow
        
        # Associate workflow with lease exit
        await self.db_tool.update_document(
            "lease_exits",
            lease_exit_id,
            {"workflow_id": workflow["id"]}
        )
        
        return workflow
    
    def _determine_workflow_steps(self, lease_type: str, property_details: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Determine the steps needed for a workflow based on lease type and property details."""
        # Common steps for all lease types
        steps = [
            {
                "id": "initiation",
                "name": "Lease Exit Initiation",
                "description": "Initial step to gather basic information about the lease exit",
                "required_form": "lease_exit_initiation",
                "assigned_role": "lease_exit_management",
                "estimated_duration_days": 1
            },
            {
                "id": "document_collection",
                "name": "Document Collection",
                "description": "Collect all relevant documents for the lease exit",
                "required_form": "document_collection",
                "assigned_role": "lease_exit_management",
                "estimated_duration_days": 3
            },
            {
                "id": "final_review",
                "name": "Final Review",
                "description": "Final review of all information and documents",
                "required_form": "final_review",
                "assigned_role": "lease_exit_management",
                "estimated_duration_days": 1
            },
            {
                "id": "approval",
                "name": "Approval",
                "description": "Approval of the lease exit",
                "required_form": "approval",
                "assigned_role": "approver",
                "estimated_duration_days": 2
            },
            {
                "id": "completion",
                "name": "Completion",
                "description": "Mark the lease exit as completed",
                "required_form": None,
                "assigned_role": "lease_exit_management",
                "estimated_duration_days": 1
            }
        ]
        
        # Add lease type specific steps
        if lease_type.lower() == "commercial":
            # Insert after document_collection
            steps.insert(2, {
                "id": "financial_analysis",
                "name": "Financial Analysis",
                "description": "Analysis of financial implications",
                "required_form": "financial_analysis",
                "assigned_role": "advisory",
                "estimated_duration_days": 5
            })
            
            # Insert after financial_analysis
            steps.insert(3, {
                "id": "property_inspection",
                "name": "Property Inspection",
                "description": "Inspection of the property condition",
                "required_form": "property_inspection",
                "assigned_role": "ifm",
                "estimated_duration_days": 3
            })
        
        # Add property type specific steps
        property_type = property_details.get("property_type", "").lower()
        if property_type == "office":
            # Insert before approval
            steps.insert(-2, {
                "id": "space_planning",
                "name": "Space Planning",
                "description": "Planning for space utilization after exit",
                "required_form": "space_planning",
                "assigned_role": "space_planning",
                "estimated_duration_days": 4
            })
        elif property_type == "retail":
            # Insert before approval
            steps.insert(-2, {
                "id": "signage_removal",
                "name": "Signage Removal Planning",
                "description": "Planning for removal of signage",
                "required_form": "signage_removal",
                "assigned_role": "ifm",
                "estimated_duration_days": 2
            })
        
        # Add legal review if needed
        if self._requires_legal_review(lease_type, property_details):
            # Insert after document_collection or financial_analysis if it exists
            insert_index = next((i for i, step in enumerate(steps) if step["id"] == "financial_analysis"), 2) + 1
            steps.insert(insert_index, {
                "id": "legal_review",
                "name": "Legal Review",
                "description": "Review of legal implications and requirements",
                "required_form": "legal_review",
                "assigned_role": "legal",
                "estimated_duration_days": 5
            })
        
        return steps
    
    def _determine_workflow_transitions(self, steps: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Determine the transitions between workflow steps."""
        transitions = []
        
        for i in range(len(steps) - 1):
            current_step = steps[i]
            next_step = steps[i + 1]
            
            transition = {
                "from_step_id": current_step["id"],
                "to_step_id": next_step["id"],
                "condition": "auto",
                "description": f"Transition from {current_step['name']} to {next_step['name']}"
            }
            
            # Add specific conditions for certain transitions
            if current_step["id"] == "approval":
                transition["condition"] = "approval_granted"
                
                # Add rejection transition
                transitions.append({
                    "from_step_id": current_step["id"],
                    "to_step_id": "document_collection",  # Go back to document collection on rejection
                    "condition": "approval_rejected",
                    "description": "Return to document collection if approval is rejected"
                })
            
            transitions.append(transition)
        
        return transitions
    
    def _estimate_workflow_duration(self, steps: List[Dict[str, Any]]) -> int:
        """Estimate the total duration of a workflow in days."""
        return sum(step.get("estimated_duration_days", 1) for step in steps)
    
    def _requires_legal_review(self, lease_type: str, property_details: Dict[str, Any]) -> bool:
        """Determine if legal review is required based on lease and property details."""
        # Logic to determine if legal review is needed
        if lease_type.lower() == "commercial":
            return True
        
        if property_details.get("value", 0) > 1000000:
            return True
            
        if property_details.get("has_special_conditions", False):
            return True
            
        return False
    
    def _apply_workflow_customizations(self, base_workflow: Dict[str, Any], customizations: Dict[str, Any]) -> Dict[str, Any]:
        """Apply customizations to a workflow."""
        result = base_workflow.copy()
        
        # Customize name and description if provided
        if "name" in customizations:
            result["name"] = customizations["name"]
        
        if "description" in customizations:
            result["description"] = customizations["description"]
        
        # Handle step additions
        if "add_steps" in customizations and isinstance(customizations["add_steps"], list):
            for step in customizations["add_steps"]:
                # Validate step
                if not all(key in step for key in ["id", "name", "assigned_role"]):
                    continue
                    
                # Add step at specified position or at the end
                if "position" in step and 0 <= step["position"] < len(result["steps"]):
                    result["steps"].insert(step["position"], step)
                else:
                    # Insert before completion step
                    completion_index = next((i for i, s in enumerate(result["steps"]) if s["id"] == "completion"), -1)
                    if completion_index >= 0:
                        result["steps"].insert(completion_index, step)
                    else:
                        result["steps"].append(step)
        
        # Handle step removals
        if "remove_step_ids" in customizations and isinstance(customizations["remove_step_ids"], list):
            result["steps"] = [step for step in result["steps"] if step["id"] not in customizations["remove_step_ids"]]
        
        # Handle step modifications
        if "modify_steps" in customizations and isinstance(customizations["modify_steps"], dict):
            for step_id, modifications in customizations["modify_steps"].items():
                for i, step in enumerate(result["steps"]):
                    if step["id"] == step_id:
                        # Apply modifications
                        for key, value in modifications.items():
                            step[key] = value
        
        # Recalculate transitions after step changes
        result["transitions"] = self._determine_workflow_transitions(result["steps"])
        
        # Update metadata
        result["metadata"] = result.get("metadata", {})
        result["metadata"]["estimated_duration_days"] = self._estimate_workflow_duration(result["steps"])
        result["metadata"]["is_customized"] = True
        
        return result
    
    def _calculate_performance_metrics(self, workflow: Dict[str, Any], lease_exits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate performance metrics for a workflow."""
        if not lease_exits:
            return {
                "total_lease_exits": 0,
                "average_completion_time_days": None,
                "completion_rate": None
            }
        
        # Calculate metrics
        total_exits = len(lease_exits)
        completed_exits = sum(1 for le in lease_exits if le.get("status") == "completed")
        
        # Calculate average completion time for completed exits
        completion_times = []
        for le in lease_exits:
            if le.get("status") == "completed" and le.get("completed_date") and le.get("created_date"):
                try:
                    # Assuming dates are stored as strings in ISO format
                    from datetime import datetime
                    completed_date = datetime.fromisoformat(le["completed_date"].replace('Z', '+00:00'))
                    created_date = datetime.fromisoformat(le["created_date"].replace('Z', '+00:00'))
                    days_to_complete = (completed_date - created_date).days
                    completion_times.append(days_to_complete)
                except (ValueError, TypeError):
                    pass
        
        avg_completion_time = sum(completion_times) / len(completion_times) if completion_times else None
        completion_rate = (completed_exits / total_exits) * 100 if total_exits > 0 else None
        
        return {
            "total_lease_exits": total_exits,
            "completed_lease_exits": completed_exits,
            "average_completion_time_days": avg_completion_time,
            "completion_rate": completion_rate,
            "expected_duration_days": workflow.get("metadata", {}).get("estimated_duration_days")
        }
    
    def _identify_bottlenecks(self, workflow: Dict[str, Any], lease_exits: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Identify bottlenecks in a workflow based on lease exit data."""
        if not lease_exits:
            return []
        
        # Group lease exits by current step
        step_distribution = {}
        for le in lease_exits:
            current_step = le.get("current_step_id")
            if current_step:
                step_distribution[current_step] = step_distribution.get(current_step, 0) + 1
        
        # Calculate average time spent in each step
        step_duration = {}
        for le in lease_exits:
            step_history = le.get("step_history", [])
            for i in range(len(step_history) - 1):
                step_id = step_history[i]["step_id"]
                start_time = datetime.fromisoformat(step_history[i]["entered_at"].replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(step_history[i+1]["entered_at"].replace('Z', '+00:00'))
                duration_days = (end_time - start_time).days
                
                if step_id not in step_duration:
                    step_duration[step_id] = []
                step_duration[step_id].append(duration_days)
        
        # Calculate average duration for each step
        avg_step_duration = {}
        for step_id, durations in step_duration.items():
            avg_step_duration[step_id] = sum(durations) / len(durations) if durations else 0
        
        # Identify bottlenecks
        bottlenecks = []
        for step in workflow.get("steps", []):
            step_id = step["id"]
            estimated_duration = step.get("estimated_duration_days", 1)
            actual_duration = avg_step_duration.get(step_id)
            
            if actual_duration and actual_duration > estimated_duration * 1.5:
                bottlenecks.append({
                    "step_id": step_id,
                    "step_name": step["name"],
                    "estimated_duration_days": estimated_duration,
                    "actual_duration_days": actual_duration,
                    "severity": "high" if actual_duration > estimated_duration * 2 else "medium",
                    "current_active_count": step_distribution.get(step_id, 0)
                })
            elif step_id in step_distribution and step_distribution[step_id] > len(lease_exits) * 0.3:
                # If more than 30% of lease exits are stuck at this step
                bottlenecks.append({
                    "step_id": step_id,
                    "step_name": step["name"],
                    "estimated_duration_days": estimated_duration,
                    "actual_duration_days": actual_duration,
                    "severity": "medium",
                    "current_active_count": step_distribution.get(step_id, 0)
                })
        
        return bottlenecks
    
    def _generate_improvement_suggestions(self, bottlenecks: List[Dict[str, Any]], 
                                          metrics: Dict[str, Any]) -> List[str]:
        """Generate suggestions for workflow improvement based on bottlenecks and metrics."""
        suggestions = []
        
        if not bottlenecks and metrics.get("completion_rate", 0) > 90:
            suggestions.append("The workflow is performing well with no significant bottlenecks.")
            return suggestions
        
        # Suggest improvements for each bottleneck
        for bottleneck in bottlenecks:
            step_id = bottleneck["step_id"]
            step_name = bottleneck["step_name"]
            severity = bottleneck["severity"]
            
            if severity == "high":
                if "approval" in step_id:
                    suggestions.append(f"Streamline the approval process in '{step_name}' by reducing the number of approvers or implementing parallel approvals.")
                elif "review" in step_id:
                    suggestions.append(f"Break down the '{step_name}' into smaller, more manageable sub-steps to reduce the overall time spent in this step.")
                else:
                    suggestions.append(f"Allocate more resources to the '{step_name}' step or simplify the requirements to reduce processing time.")
            else:
                suggestions.append(f"Consider optimizing the '{step_name}' step by providing clearer instructions or automating certain aspects.")
        
        # Overall workflow suggestions
        if metrics.get("average_completion_time_days") and metrics.get("expected_duration_days"):
            if metrics["average_completion_time_days"] > metrics["expected_duration_days"] * 1.3:
                suggestions.append("The overall workflow duration is significantly longer than expected. Consider reviewing all steps for potential optimizations.")
        
        if metrics.get("completion_rate") and metrics["completion_rate"] < 75:
            suggestions.append("The workflow has a low completion rate. Consider analyzing abandoned lease exits to identify common failure points.")
        
        return suggestions
    
    def _derive_customizations_from_lease_exit(self, lease_exit: Dict[str, Any]) -> Dict[str, Any]:
        """Derive workflow customizations based on specific lease exit details."""
        customizations = {}
        
        # Check for special requirements
        special_requirements = lease_exit.get("special_requirements", [])
        if special_requirements:
            # Handle step additions
            add_steps = []
            
            if "environmental_assessment" in special_requirements:
                add_steps.append({
                    "id": "environmental_assessment",
                    "name": "Environmental Assessment",
                    "description": "Assessment of environmental conditions and requirements",
                    "required_form": "environmental_assessment",
                    "assigned_role": "environmental_specialist",
                    "estimated_duration_days": 7
                })
            
            if "historical_preservation" in special_requirements:
                add_steps.append({
                    "id": "historical_preservation",
                    "name": "Historical Preservation Review",
                    "description": "Review of historical preservation requirements",
                    "required_form": "historical_preservation",
                    "assigned_role": "preservation_specialist",
                    "estimated_duration_days": 5
                })
            
            if add_steps:
                customizations["add_steps"] = add_steps
        
        # Modify step durations based on complexity
        complexity = lease_exit.get("complexity", "medium")
        if complexity != "medium":
            modify_steps = {}
            
            if complexity == "high":
                # Increase duration for approval and legal steps
                modify_steps["approval"] = {"estimated_duration_days": 4}  # Double the default
                modify_steps["legal_review"] = {"estimated_duration_days": 10}  # Double the default
            elif complexity == "low":
                # Decrease duration for approval and legal steps
                modify_steps["approval"] = {"estimated_duration_days": 1}  # Half the default
                modify_steps["legal_review"] = {"estimated_duration_days": 3}  # Reduced from default
            
            if modify_steps:
                customizations["modify_steps"] = modify_steps
        
        # Set custom name if special case
        if special_requirements or complexity != "medium":
            lease_type = lease_exit.get("lease_type", "standard")
            property_type = lease_exit.get("property_details", {}).get("property_type", "")
            customizations["name"] = f"Custom {complexity.title()} Complexity {lease_type.title()} {property_type.title()} Lease Exit"
        
        return customizations
