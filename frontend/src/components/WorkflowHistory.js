import React from 'react';
import {
  Box,
  Card,
  CardContent,
  CardHeader,
  Typography,
} from '@mui/material';
import Timeline from '@mui/lab/Timeline';
import TimelineItem from '@mui/lab/TimelineItem';
import TimelineOppositeContent from '@mui/lab/TimelineOppositeContent';
import TimelineSeparator from '@mui/lab/TimelineSeparator';
import TimelineDot from '@mui/lab/TimelineDot';
import TimelineConnector from '@mui/lab/TimelineConnector';
import TimelineContent from '@mui/lab/TimelineContent';
import {
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Notifications as NotificationsIcon,
  Assignment as AssignmentIcon,
  Approval as ApprovalIcon,
  Create as CreateIcon
} from '@mui/icons-material';
import { format } from 'date-fns';

/**
 * WorkflowHistory component that displays the workflow history with a timeline of events.
 */
const WorkflowHistory = ({ leaseExit }) => {
  if (!leaseExit || !leaseExit.workflow_state || !leaseExit.workflow_state.history) {
    return (
      <Card sx={{ mb: 3 }}>
        <CardHeader title="Workflow History" />
        <CardContent>
          <Typography variant="body1">
            No history available for this lease exit.
          </Typography>
        </CardContent>
      </Card>
    );
  }

  // Sort history by timestamp (newest first)
  const sortedHistory = [...leaseExit.workflow_state.history].sort((a, b) => {
    return new Date(b.timestamp) - new Date(a.timestamp);
  });

  // Get icon for a history item based on the action
  const getActionIcon = (action) => {
    if (action.includes('created')) {
      return <CreateIcon color="primary" />;
    } else if (action.includes('notification')) {
      return <NotificationsIcon color="info" />;
    } else if (action.includes('submitted')) {
      return <AssignmentIcon color="secondary" />;
    } else if (action.includes('approval_approve')) {
      return <CheckCircleIcon color="success" />;
    } else if (action.includes('approval_reject')) {
      return <CancelIcon color="error" />;
    } else if (action.includes('approval')) {
      return <ApprovalIcon color="warning" />;
    } else {
      return <AssignmentIcon color="action" />;
    }
  };

  // Get color for a timeline dot based on the action
  const getDotColor = (action) => {
    if (action.includes('created')) {
      return 'primary';
    } else if (action.includes('notification')) {
      return 'info';
    } else if (action.includes('submitted')) {
      return 'secondary';
    } else if (action.includes('approval_approve')) {
      return 'success';
    } else if (action.includes('approval_reject')) {
      return 'error';
    } else if (action.includes('approval')) {
      return 'warning';
    } else {
      return 'grey';
    }
  };

  // Format the action text for display
  const formatActionText = (action, step) => {
    if (action.includes('created')) {
      return 'Lease exit request created';
    } else if (action.includes('notification')) {
      return 'Notifications sent to stakeholders';
    } else if (action.includes('submitted')) {
      const role = action.split('_by_')[1];
      return `Form submitted by ${role}`;
    } else if (action.includes('approval_approve')) {
      return 'Approval granted';
    } else if (action.includes('approval_reject')) {
      return 'Approval rejected';
    } else if (step.includes('advisory_review')) {
      return 'Advisory review completed';
    } else if (step.includes('ifm_review')) {
      return 'IFM review completed';
    } else if (step.includes('mac_review')) {
      return 'MAC review completed';
    } else if (step.includes('pjm_review')) {
      return 'PJM review completed';
    } else {
      return action.replace(/_/g, ' ');
    }
  };

  return (
    <Card sx={{ mb: 3 }}>
      <CardHeader title="Workflow History" />
      <CardContent>
        <Timeline position="alternate">
          {sortedHistory.map((item, index) => (
            <TimelineItem key={index}>
              <TimelineOppositeContent color="text.secondary">
                {format(new Date(item.timestamp), 'MMM d, yyyy h:mm a')}
              </TimelineOppositeContent>
              <TimelineSeparator>
                <TimelineDot color={getDotColor(item.action)}>
                  {getActionIcon(item.action)}
                </TimelineDot>
                {index < sortedHistory.length - 1 && <TimelineConnector />}
              </TimelineSeparator>
              <TimelineContent>
                <Typography variant="body1">
                  {formatActionText(item.action, item.step)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {item.step.replace(/_/g, ' ')}
                </Typography>
              </TimelineContent>
            </TimelineItem>
          ))}
        </Timeline>
      </CardContent>
    </Card>
  );
};

export default WorkflowHistory; 