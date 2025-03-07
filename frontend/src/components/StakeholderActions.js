import React, { useState } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  Divider,
  Typography,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField
} from '@mui/material';
import { workflowsApi, formsApi } from '../services/api';
import DynamicForm from './DynamicForm.jsx';

/**
 * StakeholderActions component that displays the actions required by stakeholders
 * for the current workflow step.
 */
const StakeholderActions = ({ 
  leaseExit, 
  userRole = 'Advisory', // Default role for demo purposes
  onActionComplete,
  formTemplates = []
}) => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [formData, setFormData] = useState(null);
  const [showApprovalForm, setShowApprovalForm] = useState(false);
  const [approvalData, setApprovalData] = useState({
    decision: '',
    comments: ''
  });

  // Determine if the current user has actions to take based on the workflow state
  const getUserActions = () => {
    if (!leaseExit || !leaseExit.workflow_state) {
      return { hasActions: false };
    }

    const currentStep = leaseExit.workflow_state.current_step;
    
    // Check if user needs to submit a form
    if (currentStep === 'initial_submission' || currentStep === 'notifications_sent') {
      if (userRole === 'Advisory') {
        return {
          hasActions: true,
          actionType: 'form',
          formType: 'advisory_form',
          description: 'Submit Advisory Review Form'
        };
      } else if (userRole === 'IFM') {
        return {
          hasActions: true,
          actionType: 'form',
          formType: 'ifm_form',
          description: 'Submit IFM Review Form'
        };
      }
    }
    
    // Check if user needs to submit MAC form
    if (currentStep === 'ifm_review_completed') {
      if (userRole === 'MAC') {
        return {
          hasActions: true,
          actionType: 'form',
          formType: 'mac_form',
          description: 'Submit MAC Review Form'
        };
      }
    }
    
    // Check if user needs to submit PJM form
    if (currentStep === 'mac_review_completed') {
      if (userRole === 'PJM') {
        return {
          hasActions: true,
          actionType: 'form',
          formType: 'pjm_form',
          description: 'Submit PJM Review Form'
        };
      }
    }
    
    // Check if user needs to approve
    if (currentStep === 'pjm_review_completed' || 
        currentStep.startsWith('approval_') && currentStep !== 'approval_approved') {
      // Check if user has already approved
      const approvals = leaseExit.workflow_state.approvals || {};
      if (!approvals[userRole]) {
        return {
          hasActions: true,
          actionType: 'approval',
          description: 'Submit Approval Decision'
        };
      }
    }
    
    return { hasActions: false };
  };

  // Get the form template for the current action
  const getFormTemplate = (formType) => {
    const template = formTemplates.find(t => t.form_type === formType);
    
    if (!template) {
      // Return a default template if none is found
      return {
        name: formType.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()),
        description: `Form for ${formType.replace('_', ' ')}`,
        fields: [
          {
            id: "comments",
            label: "Comments",
            type: "textarea",
            required: true,
            description: "Provide your comments for this step"
          },
          {
            id: "attachments",
            label: "Attachments",
            type: "file",
            required: false,
            description: "Upload any relevant documents"
          }
        ]
      };
    }
    
    return template;
  };

  // Handle form submission
  const handleFormSubmit = async (values) => {
    const userAction = getUserActions();
    
    if (!userAction.hasActions || userAction.actionType !== 'form') {
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const formSubmission = {
        form_type: userAction.formType,
        data: values,
        submitted_by: userRole
      };
      
      const response = await workflowsApi.submitForm(leaseExit.lease_exit_id, formSubmission);
      
      setSuccess(`Form submitted successfully!`);
      
      // Notify parent component that action is complete
      if (onActionComplete) {
        onActionComplete(response.data);
      }
    } catch (err) {
      console.error("Error submitting form:", err);
      setError(`Failed to submit form: ${err.response?.data?.error || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle approval submission
  const handleApprovalSubmit = async () => {
    if (!approvalData.decision) {
      setError("Please select a decision");
      return;
    }
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      const approvalSubmission = {
        approver_id: userRole,
        decision: approvalData.decision,
        comments: approvalData.comments
      };
      
      const response = await workflowsApi.submitApproval(leaseExit.lease_exit_id, approvalSubmission);
      
      setSuccess(`Approval submitted successfully!`);
      setShowApprovalForm(false);
      
      // Notify parent component that action is complete
      if (onActionComplete) {
        onActionComplete(response.data);
      }
    } catch (err) {
      console.error("Error submitting approval:", err);
      setError(`Failed to submit approval: ${err.response?.data?.error || 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  const userAction = getUserActions();
  
  if (!userAction.hasActions) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardHeader title="Stakeholder Actions" />
        <CardContent>
          <Typography variant="body1">
            No actions required from you at this time.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ mb: 3 }}>
      <CardHeader title="Stakeholder Actions" />
      <CardContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        
        {success && (
          <Alert severity="success" sx={{ mb: 2 }}>
            {success}
          </Alert>
        )}
        
        <Typography variant="body1" gutterBottom>
          Action required: {userAction.description}
        </Typography>
        
        {userAction.actionType === 'form' && (
          <Box mt={2}>
            <DynamicForm
              formDefinition={getFormTemplate(userAction.formType)}
              onSubmit={handleFormSubmit}
              isLoading={loading}
              submitLabel="Submit Form"
            />
          </Box>
        )}
        
        {userAction.actionType === 'approval' && !showApprovalForm && (
          <Box mt={2}>
            <Button 
              variant="contained" 
              color="primary" 
              onClick={() => setShowApprovalForm(true)}
            >
              Provide Approval Decision
            </Button>
          </Box>
        )}
        
        {userAction.actionType === 'approval' && showApprovalForm && (
          <Box mt={2}>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel id="decision-label">Decision</InputLabel>
              <Select
                labelId="decision-label"
                value={approvalData.decision}
                label="Decision"
                onChange={(e) => setApprovalData({...approvalData, decision: e.target.value})}
              >
                <MenuItem value="Approve">Approve</MenuItem>
                <MenuItem value="Reject">Reject</MenuItem>
              </Select>
            </FormControl>
            
            <TextField
              fullWidth
              label="Comments"
              multiline
              rows={4}
              value={approvalData.comments}
              onChange={(e) => setApprovalData({...approvalData, comments: e.target.value})}
              sx={{ mb: 2 }}
            />
            
            <Box display="flex" justifyContent="space-between">
              <Button 
                variant="outlined" 
                onClick={() => setShowApprovalForm(false)}
                disabled={loading}
              >
                Cancel
              </Button>
              
              <Button 
                variant="contained" 
                color="primary" 
                onClick={handleApprovalSubmit}
                disabled={loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Submit Decision'}
              </Button>
            </Box>
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default StakeholderActions; 