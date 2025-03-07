import axios from 'axios';

const API_BASE_URL = '/api';

// Create axios instance with default config
const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Workflows API
export const workflowsApi = {
  // Create a new lease exit
  createLeaseExit: (data) => {
    return api.post('/workflows/lease-exit', data);
  },
  
  // Get all lease exits
  getLeaseExits: () => {
    return api.get('/workflows/lease-exits');
  },
  
  // Get a specific lease exit
  getLeaseExit: (id) => {
    return api.get(`/workflows/lease-exit/${id}`);
  },
  
  // Submit a form for a lease exit
  submitForm: (leaseExitId, formData) => {
    return api.post(`/workflows/lease-exit/${leaseExitId}/form`, formData);
  },
  
  // Submit an approval for a lease exit
  submitApproval: (leaseExitId, approvalData) => {
    return api.post(`/workflows/lease-exit/${leaseExitId}/approve`, approvalData);
  }
};

// Forms API
export const formsApi = {
  // Get all form templates
  getFormTemplates: () => {
    return api.get('/forms/templates');
  },
  
  // Create a form template
  createFormTemplate: (data) => {
    return api.post('/forms/templates', data);
  },
  
  // Get a specific form template
  getFormTemplate: (id) => {
    return api.get(`/forms/templates/${id}`);
  },
  
  // Upload a document for a lease exit
  uploadDocument: (leaseExitId, documentData) => {
    const formData = new FormData();
    for (const key in documentData) {
      formData.append(key, documentData[key]);
    }
    return api.post(`/forms/${leaseExitId}/documents`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },
  
  // Get all documents for a lease exit
  getDocuments: (leaseExitId) => {
    return api.get(`/forms/${leaseExitId}/documents`);
  },
  
  // Get all forms for a lease exit
  getForms: (leaseExitId) => {
    return api.get(`/forms/${leaseExitId}`);
  },
  
  // Get a specific form for a lease exit
  getForm: (leaseExitId, formType) => {
    return api.get(`/forms/${leaseExitId}/${formType}`);
  }
};

// Approvals API
export const approvalsApi = {
  // Process an approval
  processApproval: (leaseExitId, approvalData) => {
    return api.post(`/approvals/${leaseExitId}/process`, approvalData);
  },
  
  // Create an approval chain
  createApprovalChain: (leaseExitId, chainData) => {
    return api.post(`/approvals/${leaseExitId}/chain`, chainData);
  },
  
  // Get approval status
  getApprovalStatus: (leaseExitId) => {
    return api.get(`/approvals/${leaseExitId}/status`);
  }
};

// Notifications API
export const notificationsApi = {
  // Send notifications
  sendNotifications: (notificationData) => {
    return api.post('/notifications', notificationData);
  },
  
  // Get lease exit notifications
  getLeaseExitNotifications: (leaseExitId) => {
    return api.get(`/notifications/${leaseExitId}`);
  },
  
  // Get role notifications
  getRoleNotifications: (role) => {
    return api.get(`/notifications/role/${role}`);
  },
  
  // Resend a notification
  resendNotification: (notificationId) => {
    return api.post(`/notifications/${notificationId}/resend`);
  }
};

export default {
  workflowsApi,
  formsApi,
  approvalsApi,
  notificationsApi
}; 