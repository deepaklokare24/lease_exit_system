import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Grid, 
  Card, 
  CardContent, 
  CardHeader,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  LinearProgress
} from '@mui/material';
import { useNavigate, useLocation } from 'react-router-dom';
import { workflowsApi } from '../services/api';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Pending as PendingIcon,
  HourglassEmpty as HourglassEmptyIcon
} from '@mui/icons-material';

const Dashboard = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const [leaseExits, setLeaseExits] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [notification, setNotification] = useState(null);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    approved: 0,
    rejected: 0
  });

  useEffect(() => {
    // Check for notification in location state (from redirect)
    if (location.state?.notification) {
      setNotification(location.state.notification);
      // Clear the location state
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  useEffect(() => {
    const fetchLeaseExits = async () => {
      try {
        setLoading(true);
        const response = await workflowsApi.getLeaseExits();
        const data = response.data;
        setLeaseExits(data);
        
        // Calculate stats
        const total = data.length;
        const pending = data.filter(item => item.status === 'pending').length;
        const approved = data.filter(item => item.status === 'approved').length;
        const rejected = data.filter(item => item.status === 'rejected').length;
        
        setStats({
          total,
          pending,
          approved,
          rejected
        });
      } catch (err) {
        console.error("Error fetching lease exits:", err);
        setError("Failed to load lease exits. Please try again later.");
      } finally {
        setLoading(false);
      }
    };
    
    fetchLeaseExits();
  }, []);

  const handleNewLeaseExit = () => {
    navigate('/lease-exit-form');
  };

  const handleViewLeaseExit = (id) => {
    navigate(`/lease-exit/${id}`);
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'pending':
        return <Chip 
          icon={<PendingIcon />} 
          label="Pending" 
          color="warning" 
          size="small" 
          variant="outlined" 
        />;
      case 'approved':
        return <Chip 
          icon={<CheckCircleIcon />} 
          label="Approved" 
          color="success" 
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
      case 'in_progress':
        return <Chip 
          icon={<HourglassEmptyIcon />} 
          label="In Progress" 
          color="primary" 
          size="small" 
          variant="outlined" 
        />;
      default:
        return <Chip 
          label={status} 
          color="default" 
          size="small" 
          variant="outlined" 
        />;
    }
  };

  // Get the workflow progress percentage based on the current step
  const getWorkflowProgress = (leaseExit) => {
    if (!leaseExit || !leaseExit.workflow_state) {
      return 0;
    }

    const steps = [
      'initial_submission',
      'notifications_sent',
      'advisory_review_completed',
      'ifm_review_completed',
      'mac_review_completed',
      'pjm_review_completed',
      'approval_approved'
    ];
    
    const currentStep = leaseExit.workflow_state.current_step;
    const currentStepIndex = steps.indexOf(currentStep);
    
    if (currentStepIndex < 0) {
      return 0;
    }
    
    return Math.round((currentStepIndex / (steps.length - 1)) * 100);
  };

  // Get the current workflow step in a readable format
  const getWorkflowStepLabel = (leaseExit) => {
    if (!leaseExit || !leaseExit.workflow_state) {
      return 'Not Started';
    }

    const currentStep = leaseExit.workflow_state.current_step;
    
    if (currentStep === 'initial_submission') {
      return 'Initial Submission';
    } else if (currentStep === 'notifications_sent') {
      return 'Notifications Sent';
    } else if (currentStep === 'advisory_review_completed') {
      return 'Advisory Review Completed';
    } else if (currentStep === 'ifm_review_completed') {
      return 'IFM Review Completed';
    } else if (currentStep === 'mac_review_completed') {
      return 'MAC Review Completed';
    } else if (currentStep === 'pjm_review_completed') {
      return 'PJM Review Completed';
    } else if (currentStep === 'approval_approved') {
      return 'Approved';
    } else if (currentStep === 'approval_rejected') {
      return 'Rejected';
    } else {
      return currentStep.replace(/_/g, ' ');
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Lease Exit Dashboard</Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={handleNewLeaseExit}
        >
          New Lease Exit
        </Button>
      </Box>
      
      {notification && (
        <Alert 
          severity={notification.type || "success"} 
          sx={{ mb: 3 }}
          onClose={() => setNotification(null)}
        >
          {typeof notification === 'object' ? notification.message : notification}
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
      
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Total Lease Exits</Typography>
              <Typography variant="h3">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Pending</Typography>
              <Typography variant="h3">{stats.pending}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Approved</Typography>
              <Typography variant="h3">{stats.approved}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Rejected</Typography>
              <Typography variant="h3">{stats.rejected}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      
      <Paper sx={{ width: '100%', overflow: 'hidden' }}>
        <TableContainer sx={{ maxHeight: 440 }}>
          {loading ? (
            <Box p={3} textAlign="center">
              <CircularProgress />
            </Box>
          ) : leaseExits.length > 0 ? (
            <Table stickyHeader>
              <TableHead>
                <TableRow>
                  <TableCell>Lease Exit ID</TableCell>
                  <TableCell>Property</TableCell>
                  <TableCell>Exit Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Workflow Progress</TableCell>
                  <TableCell>Current Step</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {leaseExits.map((leaseExit) => (
                  <TableRow key={leaseExit.lease_exit_id || leaseExit._id}>
                    <TableCell>{leaseExit.lease_exit_id}</TableCell>
                    <TableCell>{leaseExit.property_details?.property_address || 'N/A'}</TableCell>
                    <TableCell>
                      {leaseExit.exit_details?.exit_date 
                        ? new Date(leaseExit.exit_details.exit_date).toLocaleDateString() 
                        : 'N/A'
                      }
                    </TableCell>
                    <TableCell>{getStatusChip(leaseExit.status)}</TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={getWorkflowProgress(leaseExit)} 
                            color={
                              leaseExit.status === 'rejected' ? 'error' : 
                              leaseExit.status === 'approved' ? 'success' : 'primary'
                            }
                          />
                        </Box>
                        <Box sx={{ minWidth: 35 }}>
                          <Typography variant="body2" color="text.secondary">
                            {`${getWorkflowProgress(leaseExit)}%`}
                          </Typography>
                        </Box>
                      </Box>
                    </TableCell>
                    <TableCell>{getWorkflowStepLabel(leaseExit)}</TableCell>
                    <TableCell>
                      <Button 
                        variant="outlined" 
                        size="small" 
                        onClick={() => handleViewLeaseExit(leaseExit.lease_exit_id || leaseExit._id)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          ) : (
            <Box p={3} textAlign="center">
              <Typography variant="body1">
                No lease exits found. Create a new lease exit to get started.
              </Typography>
            </Box>
          )}
        </TableContainer>
      </Paper>
    </Box>
  );
};

export default Dashboard; 