import React from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Typography,
  Paper,
  Chip
} from '@mui/material';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  HourglassEmpty as HourglassEmptyIcon
} from '@mui/icons-material';

/**
 * WorkflowStatusTracker component that visualizes the lease exit workflow progress
 * with steps and status indicators.
 */
const WorkflowStatusTracker = ({ leaseExit }) => {
  // Define the workflow steps based on the lease exit workflow
  const workflowSteps = [
    {
      label: 'Initial Submission',
      description: 'Lease exit request submitted by Lease Exit Management Team',
      status: 'completed', // Always completed if we have a lease exit
    },
    {
      label: 'Notifications Sent',
      description: 'Notifications sent to Advisory, IFM, and Legal',
      status: getStepStatus('notifications_sent', leaseExit),
    },
    {
      label: 'Advisory Review',
      description: 'Advisory team reviews the lease exit request',
      status: getStepStatus('advisory_review_completed', leaseExit),
    },
    {
      label: 'IFM Review',
      description: 'IFM team reviews the lease exit request',
      status: getStepStatus('ifm_review_completed', leaseExit),
    },
    {
      label: 'MAC Review',
      description: 'MAC team reviews the lease exit request',
      status: getStepStatus('mac_review_completed', leaseExit),
    },
    {
      label: 'PJM Review',
      description: 'PJM team reviews the lease exit request',
      status: getStepStatus('pjm_review_completed', leaseExit),
    },
    {
      label: 'Final Approval',
      description: 'Final approval by all stakeholders',
      status: getStepStatus('approval_approved', leaseExit),
    }
  ];

  // Get the active step based on the current workflow state
  const getActiveStep = () => {
    const currentStep = leaseExit?.workflow_state?.current_step || 'initial_submission';
    
    // Find the index of the current step in the workflow steps
    const activeStepIndex = workflowSteps.findIndex(step => {
      return step.label.toLowerCase().replace(' ', '_') === currentStep.replace('_completed', '');
    });
    
    // If not found, return 0 (initial submission)
    return activeStepIndex >= 0 ? activeStepIndex : 0;
  };

  // Get the status chip for a step
  const getStatusChip = (status) => {
    switch (status) {
      case 'completed':
        return <Chip 
          icon={<CheckCircleIcon />} 
          label="Completed" 
          color="success" 
          size="small" 
          variant="outlined" 
        />;
      case 'in_progress':
        return <Chip 
          icon={<HourglassEmptyIcon />} 
          label="In Progress" 
          color="primary" 
          size="small" 
          variant="outlined" 
        />;
      case 'pending':
        return <Chip 
          icon={<PendingIcon />} 
          label="Pending" 
          color="warning" 
          size="small" 
          variant="outlined" 
        />;
      case 'rejected':
        return <Chip 
          icon={<CancelIcon />} 
          label="Rejected" 
          color="error" 
          size="small" 
          variant="outlined" 
        />;
      default:
        return <Chip 
          icon={<PendingIcon />} 
          label="Not Started" 
          color="default" 
          size="small" 
          variant="outlined" 
        />;
    }
  };

  return (
    <Paper elevation={0} sx={{ p: 3, mb: 3 }}>
      <Typography variant="h6" gutterBottom>
        Workflow Progress
      </Typography>
      <Stepper activeStep={getActiveStep()} orientation="vertical">
        {workflowSteps.map((step, index) => (
          <Step key={step.label}>
            <StepLabel
              optional={
                <Box sx={{ display: 'flex', alignItems: 'center', mt: 0.5 }}>
                  {getStatusChip(step.status)}
                </Box>
              }
            >
              {step.label}
            </StepLabel>
            <StepContent>
              <Typography variant="body2" color="text.secondary">
                {step.description}
              </Typography>
              {step.status === 'rejected' && (
                <Typography variant="body2" color="error" sx={{ mt: 1 }}>
                  This step was rejected. The workflow needs to be revised.
                </Typography>
              )}
            </StepContent>
          </Step>
        ))}
      </Stepper>
    </Paper>
  );
};

// Helper function to determine the status of a step based on the lease exit data
function getStepStatus(stepKey, leaseExit) {
  if (!leaseExit || !leaseExit.workflow_state) {
    return 'not_started';
  }

  const currentStep = leaseExit.workflow_state.current_step;
  const history = leaseExit.workflow_state.history || [];
  
  // Check if this step is in the history
  const stepInHistory = history.some(item => item.step === stepKey);
  
  if (stepInHistory) {
    return 'completed';
  }
  
  // Check if this is the current step
  if (currentStep === stepKey) {
    return 'in_progress';
  }
  
  // Check if the workflow is rejected
  if (leaseExit.status === 'rejected') {
    return 'rejected';
  }
  
  // Check if this step is pending (comes after the current step)
  const steps = [
    'initial_submission',
    'notifications_sent',
    'advisory_review_completed',
    'ifm_review_completed',
    'mac_review_completed',
    'pjm_review_completed',
    'approval_approved'
  ];
  
  const currentStepIndex = steps.indexOf(currentStep);
  const thisStepIndex = steps.indexOf(stepKey);
  
  if (currentStepIndex < thisStepIndex) {
    return 'pending';
  }
  
  return 'not_started';
}

export default WorkflowStatusTracker; 