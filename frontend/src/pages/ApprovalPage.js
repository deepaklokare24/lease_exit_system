import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  Button, 
  List, 
  ListItem, 
  ListItemText, 
  Divider, 
  Chip, 
  TextField, 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogContentText, 
  DialogActions,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  CardHeader,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { workflowsApi } from '../services/api';

const ApprovalPage = () => {
  const navigate = useNavigate();
  const [pendingApprovals, setPendingApprovals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedApproval, setSelectedApproval] = useState(null);
  const [decision, setDecision] = useState('');
  const [comments, setComments] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submitSuccess, setSubmitSuccess] = useState(null);
  const [userRole, setUserRole] = useState('Advisory'); // Default role for demo purposes

  useEffect(() => {
    const fetchPendingApprovals = async () => {
      try {
        setLoading(true);
        
        // Get all lease exits
        const response = await workflowsApi.getLeaseExits();
        const leaseExits = response.data;
        
        // Filter for lease exits that need approval
        const needsApproval = leaseExits.filter(leaseExit => {
          // Check if the lease exit is in a state that requires approval
          const currentStep = leaseExit.workflow_state?.current_step || '';
          return (
            currentStep === 'pjm_review_completed' || 
            (currentStep.startsWith('approval_') && currentStep !== 'approval_approved' && currentStep !== 'approval_rejected')
          );
        });
        
        setPendingApprovals(needsApproval);
      } catch (err) {
        console.error("Error fetching pending approvals:", err);
        setError("Failed to load pending approvals. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchPendingApprovals();
  }, []);

  const handleViewLeaseExit = (id) => {
    navigate(`/lease-exit/${id}`);
  };

  const handleOpenDialog = (leaseExitId) => {
    const leaseExit = pendingApprovals.find(item => item.lease_exit_id === leaseExitId);
    setSelectedApproval(leaseExit);
    setDialogOpen(true);
    setDecision('');
    setComments('');
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setSelectedApproval(null);
    setDecision('');
    setComments('');
    setSubmitError(null);
  };

  const handleSubmitApproval = async () => {
    if (!decision) {
      setSubmitError("Please select a decision");
      return;
    }
    
    try {
      setSubmitting(true);
      setSubmitError(null);
      
      const approvalData = {
        approver_id: userRole,
        decision: decision,
        comments: comments
      };
      
      await workflowsApi.submitApproval(selectedApproval.lease_exit_id, approvalData);
      
      setSubmitSuccess(`Approval submitted successfully!`);
      setDialogOpen(false);
      
      // Refresh the pending approvals list
      const response = await workflowsApi.getLeaseExits();
      const leaseExits = response.data;
      
      // Filter for lease exits that need approval
      const needsApproval = leaseExits.filter(leaseExit => {
        const currentStep = leaseExit.workflow_state?.current_step || '';
        return (
          currentStep === 'pjm_review_completed' || 
          (currentStep.startsWith('approval_') && currentStep !== 'approval_approved' && currentStep !== 'approval_rejected')
        );
      });
      
      setPendingApprovals(needsApproval);
    } catch (err) {
      console.error("Error submitting approval:", err);
      setSubmitError(`Failed to submit approval: ${err.response?.data?.error || 'Unknown error'}`);
    } finally {
      setSubmitting(false);
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
      default:
        return <Chip label={status} color="default" />;
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Approval Requests</Typography>
      </Box>
      
      {submitSuccess && (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          onClose={() => setSubmitSuccess(null)}
        >
          {submitSuccess}
        </Alert>
      )}
      
      {error && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          onClose={() => setError(null)}
        >
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Paper>
            {loading ? (
              <Box p={3} textAlign="center">
                <CircularProgress />
              </Box>
            ) : pendingApprovals.length > 0 ? (
              <List>
                {pendingApprovals.map((leaseExit) => (
                  <React.Fragment key={leaseExit.lease_exit_id}>
                    <ListItem>
                      <ListItemText
                        primary={`Lease Exit: ${leaseExit.lease_exit_id}`}
                        secondary={`Property: ${leaseExit.property_details?.property_address || 'N/A'}`}
                      />
                      <Box>
                        <Button 
                          variant="outlined" 
                          size="small" 
                          sx={{ mr: 1 }}
                          onClick={() => handleViewLeaseExit(leaseExit.lease_exit_id)}
                        >
                          View Details
                        </Button>
                        <Button 
                          variant="contained" 
                          color="primary" 
                          size="small"
                          onClick={() => handleOpenDialog(leaseExit.lease_exit_id)}
                        >
                          Provide Approval
                        </Button>
                      </Box>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box p={3} textAlign="center">
                <Typography variant="body1">
                  No pending approvals found.
                </Typography>
              </Box>
            )}
          </Paper>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Card>
            <CardHeader title="Role Selector (Demo)" />
            <CardContent>
              <Typography variant="body2" gutterBottom>
                For demonstration purposes, select a role to view different approval actions:
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
                  variant={userRole === 'Lease Exit Management' ? 'contained' : 'outlined'} 
                  onClick={() => setUserRole('Lease Exit Management')}
                  sx={{ mr: 1, mb: 1 }}
                >
                  Lease Exit Management
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Dialog open={dialogOpen} onClose={handleCloseDialog} maxWidth="sm" fullWidth>
        <DialogTitle>Provide Approval Decision</DialogTitle>
        <DialogContent>
          {submitError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {submitError}
            </Alert>
          )}
          
          {selectedApproval && (
            <>
              <DialogContentText gutterBottom>
                You are providing an approval decision for lease exit {selectedApproval.lease_exit_id}.
              </DialogContentText>
              
              <Box mt={2}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel id="decision-label">Decision</InputLabel>
                  <Select
                    labelId="decision-label"
                    value={decision}
                    label="Decision"
                    onChange={(e) => setDecision(e.target.value)}
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
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                />
              </Box>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog} disabled={submitting}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmitApproval} 
            variant="contained" 
            color="primary"
            disabled={submitting}
          >
            {submitting ? <CircularProgress size={24} /> : 'Submit'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ApprovalPage; 