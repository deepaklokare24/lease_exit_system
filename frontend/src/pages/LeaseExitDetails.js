import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  Grid, 
  Chip, 
  Divider, 
  CircularProgress, 
  Alert,
  Card,
  CardContent,
  CardHeader,
  List,
  ListItem,
  ListItemText,
  Tab,
  Tabs
} from '@mui/material';
import { useParams, useNavigate } from 'react-router-dom';
import { workflowsApi, formsApi, approvalsApi, notificationsApi } from '../services/api';
import DynamicForm from '../components/DynamicForm';
import WorkflowStatusTracker from '../components/WorkflowStatusTracker';
import StakeholderActions from '../components/StakeholderActions';
import WorkflowHistory from '../components/WorkflowHistory';

const LeaseExitDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [leaseExit, setLeaseExit] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [tabValue, setTabValue] = useState(0);
  const [forms, setForms] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [formTemplates, setFormTemplates] = useState([]);
  const [formLoading, setFormLoading] = useState(false);
  const [formError, setFormError] = useState(null);
  const [formSuccess, setFormSuccess] = useState(null);
  const [userRole, setUserRole] = useState('Advisory'); // Default role for demo purposes

  useEffect(() => {
    const fetchLeaseExitDetails = async () => {
      try {
        setLoading(true);
        
        // Fetch lease exit details
        const leaseExitResponse = await workflowsApi.getLeaseExit(id);
        setLeaseExit(leaseExitResponse.data);
        
        // Fetch forms
        try {
          const formsResponse = await formsApi.getForms(id);
          setForms(formsResponse.data);
        } catch (err) {
          console.error("Error fetching forms:", err);
          // Non-critical error, continue
        }
        
        // Fetch documents
        try {
          const documentsResponse = await formsApi.getDocuments(id);
          setDocuments(documentsResponse.data);
        } catch (err) {
          console.error("Error fetching documents:", err);
          // Non-critical error, continue
        }
        
        // Fetch notifications
        try {
          const notificationsResponse = await notificationsApi.getLeaseExitNotifications(id);
          setNotifications(notificationsResponse.data);
        } catch (err) {
          console.error("Error fetching notifications:", err);
          // Non-critical error, continue
        }
        
        // Fetch form templates
        try {
          const templatesResponse = await formsApi.getFormTemplates();
          setFormTemplates(templatesResponse.data);
        } catch (err) {
          console.error("Error fetching form templates:", err);
          // Non-critical error, continue
        }
        
      } catch (err) {
        console.error("Error fetching lease exit details:", err);
        setError("Failed to load lease exit details. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchLeaseExitDetails();
  }, [id]);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  const handleBackToDashboard = () => {
    navigate('/');
  };

  const handleActionComplete = async () => {
    // Refresh the lease exit details
    try {
      setLoading(true);
      const leaseExitResponse = await workflowsApi.getLeaseExit(id);
      setLeaseExit(leaseExitResponse.data);
      setFormSuccess("Action completed successfully!");
    } catch (err) {
      console.error("Error refreshing lease exit details:", err);
      setFormError("Action completed but failed to refresh details.");
    } finally {
      setLoading(false);
    }
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip label="Pending" color="warning" />;
      case 'approved':
        return <Chip label="Approved" color="success" />;
      case 'rejected':
        return <Chip label="Rejected" color="error" />;
      case 'completed':
        return <Chip label="Completed" color="success" />;
      default:
        return <Chip label={status} color="default" />;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="80vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box m={3}>
        <Alert severity="error">{error}</Alert>
        <Box mt={2}>
          <Button variant="contained" onClick={handleBackToDashboard}>
            Back to Dashboard
          </Button>
        </Box>
      </Box>
    );
  }

  if (!leaseExit) {
    return (
      <Box m={3}>
        <Alert severity="warning">Lease exit not found.</Alert>
        <Box mt={2}>
          <Button variant="contained" onClick={handleBackToDashboard}>
            Back to Dashboard
          </Button>
        </Box>
      </Box>
    );
  }

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Lease Exit Details</Typography>
        <Button variant="outlined" onClick={handleBackToDashboard}>
          Back to Dashboard
        </Button>
      </Box>
      
      {formSuccess && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setFormSuccess(null)}>
          {formSuccess}
        </Alert>
      )}
      
      {formError && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setFormError(null)}>
          {formError}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          {/* Main content */}
          <Card sx={{ mb: 3 }}>
            <CardHeader 
              title={`Lease Exit: ${leaseExit.lease_exit_id}`}
              subheader={`Status: ${leaseExit.status}`}
              action={getStatusChip(leaseExit.status)}
            />
            <CardContent>
              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1">Property Address</Typography>
                  <Typography variant="body1" gutterBottom>
                    {leaseExit.property_details?.property_address || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1">Lease ID</Typography>
                  <Typography variant="body1" gutterBottom>
                    {leaseExit.property_details?.lease_id || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1">Exit Date</Typography>
                  <Typography variant="body1" gutterBottom>
                    {new Date(leaseExit.exit_details?.exit_date).toLocaleDateString() || 'N/A'}
                  </Typography>
                </Grid>
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle1">Reason for Exit</Typography>
                  <Typography variant="body1" gutterBottom>
                    {leaseExit.exit_details?.reason_for_exit || 'N/A'}
                  </Typography>
                </Grid>
                {leaseExit.exit_details?.additional_notes && (
                  <Grid item xs={12}>
                    <Typography variant="subtitle1">Additional Notes</Typography>
                    <Typography variant="body1" gutterBottom>
                      {leaseExit.exit_details.additional_notes}
                    </Typography>
                  </Grid>
                )}
              </Grid>
            </CardContent>
          </Card>
          
          {/* Workflow Status Tracker */}
          <WorkflowStatusTracker leaseExit={leaseExit} />
          
          {/* Stakeholder Actions */}
          <StakeholderActions 
            leaseExit={leaseExit} 
            userRole={userRole} 
            onActionComplete={handleActionComplete}
            formTemplates={formTemplates}
          />
          
          {/* Workflow History */}
          <WorkflowHistory leaseExit={leaseExit} />
          
          {/* Tabs for additional information */}
          <Paper sx={{ mb: 3 }}>
            <Tabs
              value={tabValue}
              onChange={handleTabChange}
              indicatorColor="primary"
              textColor="primary"
              variant="fullWidth"
            >
              <Tab label="Forms" />
              <Tab label="Documents" />
              <Tab label="Notifications" />
            </Tabs>
            <Box p={3}>
              {tabValue === 0 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Submitted Forms
                  </Typography>
                  {forms.length > 0 ? (
                    <List>
                      {forms.map((form, index) => (
                        <ListItem key={index} divider={index < forms.length - 1}>
                          <ListItemText
                            primary={form.form_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                            secondary={`Submitted by: ${form.submitted_by} on ${new Date(form.created_at).toLocaleString()}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1">No forms submitted yet.</Typography>
                  )}
                </Box>
              )}
              
              {tabValue === 1 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Documents
                  </Typography>
                  {documents.length > 0 ? (
                    <List>
                      {documents.map((doc, index) => (
                        <ListItem key={index} divider={index < documents.length - 1}>
                          <ListItemText
                            primary={doc.filename}
                            secondary={`Uploaded by: ${doc.uploaded_by} on ${new Date(doc.uploaded_at).toLocaleString()}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1">No documents uploaded yet.</Typography>
                  )}
                </Box>
              )}
              
              {tabValue === 2 && (
                <Box>
                  <Typography variant="h6" gutterBottom>
                    Notifications
                  </Typography>
                  {notifications.length > 0 ? (
                    <List>
                      {notifications.map((notification, index) => (
                        <ListItem key={index} divider={index < notifications.length - 1}>
                          <ListItemText
                            primary={notification.subject}
                            secondary={`Sent to: ${notification.recipient_role} on ${new Date(notification.created_at).toLocaleString()}`}
                          />
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography variant="body1">No notifications sent yet.</Typography>
                  )}
                </Box>
              )}
            </Box>
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          {/* Sidebar */}
          <Card sx={{ mb: 3 }}>
            <CardHeader title="Role Selector (Demo)" />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                For demonstration purposes, select a role to view different stakeholder actions:
              </Typography>
              <Box mt={2}>
                <Button 
                  variant={userRole === 'Advisory' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('Advisory')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Advisory
                </Button>
                <Button 
                  variant={userRole === 'IFM' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('IFM')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  IFM
                </Button>
                <Button 
                  variant={userRole === 'Legal' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('Legal')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Legal
                </Button>
                <Button 
                  variant={userRole === 'MAC' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('MAC')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  MAC
                </Button>
                <Button 
                  variant={userRole === 'PJM' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('PJM')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  PJM
                </Button>
                <Button 
                  variant={userRole === 'Lease Exit Management' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('Lease Exit Management')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Lease Exit Management
                </Button>
              </Box>
            </CardContent>
          </Card>
          
          <Card>
            <CardHeader title="Approvals" />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                Approval status for this lease exit:
              </Typography>
              <List>
                {Object.entries(leaseExit.workflow_state?.approvals || {}).map(([role, approval], index) => (
                  <ListItem key={role} divider={index < Object.keys(leaseExit.workflow_state?.approvals || {}).length - 1}>
                    <ListItemText
                      primary={`${role}: ${approval.decision}`}
                      secondary={`Comments: ${approval.comments || 'None'}`}
                    />
                  </ListItem>
                ))}
                {Object.keys(leaseExit.workflow_state?.approvals || {}).length === 0 && (
                  <Typography variant="body1">No approvals submitted yet.</Typography>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default LeaseExitDetails; 