import React, { useState, useEffect } from 'react';
import { Typography, Box, Paper, CircularProgress, Alert } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import DynamicForm from '../components/DynamicForm';
import { workflowsApi, formsApi } from '../services/api';

const LeaseExitForm = () => {
  const navigate = useNavigate();
  const [formDefinition, setFormDefinition] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const fetchFormTemplate = async () => {
      try {
        setLoading(true);
        // Get the lease exit initiation form template
        const response = await formsApi.getFormTemplates();
        const templates = response.data;
        
        // Find the lease exit initiation template
        const initiationTemplate = templates.find(template => 
          template.form_type === 'lease_exit_initiation'
        );
        
        if (initiationTemplate) {
          setFormDefinition(initiationTemplate);
        } else {
          // If no template exists, use a default form definition
          setFormDefinition({
            name: "Lease Exit Initiation",
            description: "Form to initiate a new lease exit process",
            fields: [
              {
                id: "lease_id",
                label: "Lease ID",
                type: "text",
                required: true,
                description: "Unique identifier for the lease"
              },
              {
                id: "property_address",
                label: "Property Address",
                type: "text",
                required: true,
                description: "Address of the property"
              },
              {
                id: "exit_date",
                label: "Expected Exit Date",
                type: "date",
                required: true,
                description: "The date when the lease exit should be completed"
              },
              {
                id: "reason_for_exit",
                label: "Exit Reason",
                type: "select",
                options: ["End of Term", "Early Termination", "Breach of Contract", "Other"],
                required: true
              },
              {
                id: "additional_notes",
                label: "Additional Notes",
                type: "textarea",
                required: false,
                description: "Any additional information about the lease exit"
              }
            ]
          });
        }
      } catch (err) {
        console.error("Error fetching form template:", err);
        setError("Failed to load form template. Please try again later.");
        
        // Use default form definition as fallback
        setFormDefinition({
          name: "Lease Exit Initiation",
          description: "Form to initiate a new lease exit process",
          fields: [
            {
              id: "lease_id",
              label: "Lease ID",
              type: "text",
              required: true,
              description: "Unique identifier for the lease"
            },
            {
              id: "property_address",
              label: "Property Address",
              type: "text",
              required: true,
              description: "Address of the property"
            },
            {
              id: "exit_date",
              label: "Expected Exit Date",
              type: "date",
              required: true,
              description: "The date when the lease exit should be completed"
            },
            {
              id: "reason_for_exit",
              label: "Exit Reason",
              type: "select",
              options: ["End of Term", "Early Termination", "Breach of Contract", "Other"],
              required: true
            },
            {
              id: "additional_notes",
              label: "Additional Notes",
              type: "textarea",
              required: false,
              description: "Any additional information about the lease exit"
            }
          ]
        });
      } finally {
        setLoading(false);
      }
    };

    fetchFormTemplate();
  }, []);

  const handleSubmit = async (values) => {
    try {
      setSubmitting(true);
      setError(null);
      
      // Submit the form data to create a new lease exit
      const response = await workflowsApi.createLeaseExit(values);
      
      // Navigate to the dashboard with a success message
      navigate('/', { 
        state: { 
          notification: {
            type: 'success',
            message: 'Lease exit process initiated successfully'
          }
        }
      });
    } catch (err) {
      console.error("Error submitting form:", err);
      const errorMessage = err.response?.data?.error || "Failed to submit form. Please try again later.";
      setError(errorMessage);
    } finally {
      setSubmitting(false);
    }
  };

  const handleCancel = () => {
    navigate('/');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Typography variant="h4" gutterBottom>New Lease Exit Request</Typography>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Paper sx={{ p: 3, mt: 2 }}>
        {formDefinition ? (
          <DynamicForm
            formDefinition={formDefinition}
            onSubmit={handleSubmit}
            onCancel={handleCancel}
            submitLabel="Submit Request"
            cancelLabel="Cancel"
            isLoading={submitting}
          />
        ) : (
          <Typography variant="body1" color="error">
            Unable to load form. Please try again later.
          </Typography>
        )}
      </Paper>
    </Box>
  );
};

export default LeaseExitForm; 