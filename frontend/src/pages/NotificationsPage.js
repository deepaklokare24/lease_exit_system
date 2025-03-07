import React, { useState, useEffect } from 'react';
import { 
  Typography, 
  Box, 
  Paper, 
  List, 
  ListItem, 
  ListItemText, 
  Chip, 
  Button, 
  CircularProgress, 
  Alert,
  Divider,
  IconButton,
  Tooltip,
  Card,
  CardContent,
  CardHeader,
  Grid
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { notificationsApi, workflowsApi } from '../services/api';
import { useNavigate } from 'react-router-dom';

const NotificationsPage = () => {
  const navigate = useNavigate();
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [resending, setResending] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(null);
  const [resendError, setResendError] = useState(null);
  const [userRole, setUserRole] = useState('Advisory'); // Default role for demo purposes

  const fetchNotifications = async () => {
    try {
      setLoading(true);
      
      // Get all lease exits to extract notifications
      const response = await workflowsApi.getLeaseExits();
      const leaseExits = response.data;
      
      // Extract notifications from lease exits
      let allNotifications = [];
      
      // In a real application, you would have a dedicated API endpoint for notifications
      // For now, we'll simulate by extracting from workflow history
      for (const leaseExit of leaseExits) {
        if (leaseExit.workflow_state && leaseExit.workflow_state.history) {
          const notificationEvents = leaseExit.workflow_state.history.filter(
            item => item.action.includes('notification') || item.step.includes('notification')
          );
          
          for (const event of notificationEvents) {
            allNotifications.push({
              id: `${leaseExit.lease_exit_id}-${event.timestamp}`,
              lease_exit_id: leaseExit.lease_exit_id,
              subject: `Lease Exit Update - ${leaseExit.lease_exit_id}`,
              message: `Update for lease exit at ${leaseExit.property_details?.property_address || 'Unknown Address'}`,
              recipient_role: userRole,
              status: 'sent',
              created_at: event.timestamp,
              property_address: leaseExit.property_details?.property_address || 'Unknown Address'
            });
          }
        }
      }
      
      // Sort notifications by date (newest first)
      allNotifications.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      // Filter notifications for the current user role
      const userNotifications = allNotifications.filter(
        notification => notification.recipient_role === userRole
      );
      
      setNotifications(userNotifications);
    } catch (err) {
      console.error("Error fetching notifications:", err);
      setError("Failed to load notifications. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNotifications();
  }, [userRole]);

  const handleResendNotification = async (notificationId) => {
    try {
      setResending(true);
      setResendError(null);
      setResendSuccess(null);
      
      // In a real application, you would call the API to resend the notification
      // For now, we'll simulate a successful resend
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      setResendSuccess(`Notification resent successfully!`);
    } catch (err) {
      console.error("Error resending notification:", err);
      setResendError("Failed to resend notification. Please try again later.");
    } finally {
      setResending(false);
    }
  };

  const handleRefresh = () => {
    fetchNotifications();
  };

  const handleViewLeaseExit = (leaseExitId) => {
    navigate(`/lease-exit/${leaseExitId}`);
  };

  const getStatusChip = (status) => {
    switch (status) {
      case 'sent':
        return <Chip label="Sent" color="success" size="small" />;
      case 'failed':
        return <Chip label="Failed" color="error" size="small" />;
      case 'pending':
        return <Chip label="Pending" color="warning" size="small" />;
      default:
        return <Chip label={status} color="default" size="small" />;
    }
  };

  return (
    <Box p={3}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Notifications</Typography>
        <Tooltip title="Refresh notifications">
          <IconButton onClick={handleRefresh} disabled={loading}>
            <RefreshIcon />
          </IconButton>
        </Tooltip>
      </Box>
      
      {resendSuccess && (
        <Alert 
          severity="success" 
          sx={{ mb: 3 }}
          onClose={() => setResendSuccess(null)}
        >
          {resendSuccess}
        </Alert>
      )}
      
      {resendError && (
        <Alert 
          severity="error" 
          sx={{ mb: 3 }}
          onClose={() => setResendError(null)}
        >
          {resendError}
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
            ) : notifications.length > 0 ? (
              <List>
                {notifications.map((notification) => (
                  <React.Fragment key={notification.id}>
                    <ListItem>
                      <ListItemText
                        primary={notification.subject}
                        secondary={
                          <>
                            <Typography variant="body2" component="span">
                              {`Property: ${notification.property_address}`}
                            </Typography>
                            <br />
                            <Typography variant="body2" component="span" color="text.secondary">
                              {`Sent: ${new Date(notification.created_at).toLocaleString()}`}
                            </Typography>
                          </>
                        }
                      />
                      <Box>
                        {getStatusChip(notification.status)}
                        <Box mt={1}>
                          <Button 
                            variant="outlined" 
                            size="small" 
                            sx={{ mr: 1 }}
                            onClick={() => handleViewLeaseExit(notification.lease_exit_id)}
                          >
                            View Lease Exit
                          </Button>
                          {notification.status === 'failed' && (
                            <Button 
                              variant="contained" 
                              color="primary" 
                              size="small"
                              onClick={() => handleResendNotification(notification.id)}
                              disabled={resending}
                            >
                              Resend
                            </Button>
                          )}
                        </Box>
                      </Box>
                    </ListItem>
                    <Divider />
                  </React.Fragment>
                ))}
              </List>
            ) : (
              <Box p={3} textAlign="center">
                <Typography variant="body1">
                  No notifications found for your role.
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
                For demonstration purposes, select a role to view different notifications:
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
        </Grid>
      </Grid>
    </Box>
  );
};

export default NotificationsPage; 