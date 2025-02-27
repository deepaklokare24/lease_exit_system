import React, { useState, useEffect } from 'react';
import { useFormik } from 'formik';
import * as yup from 'yup';
import {
  Box,
  Button,
  Card,
  CardContent,
  CardHeader,
  CircularProgress,
  Divider,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Typography,
  Alert,
} from '@mui/material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';

/**
 * DynamicForm component that renders a form based on a provided form definition
 * and handles submission and validation.
 */
const DynamicForm = ({ 
  formDefinition, 
  initialValues = {}, 
  onSubmit, 
  onCancel,
  submitLabel = "Submit",
  cancelLabel = "Cancel",
  isLoading = false,
  isReadOnly = false,
}) => {
  const [validationSchema, setValidationSchema] = useState(null);
  const [formFields, setFormFields] = useState([]);
  const [formError, setFormError] = useState(null);

  // Create validation schema based on form definition
  useEffect(() => {
    if (!formDefinition || !formDefinition.fields) {
      setFormError("Invalid form definition");
      return;
    }

    try {
      const fields = formDefinition.fields;
      setFormFields(fields);

      // Build Yup validation schema
      let schemaObj = {};
      const validationRules = formDefinition.validation_rules || {};

      fields.forEach(field => {
        const fieldId = field.id;
        const fieldRules = validationRules[fieldId] || {};
        let fieldSchema;

        switch (field.type) {
          case 'text':
          case 'textarea':
            fieldSchema = yup.string();
            if (fieldRules.min_length) {
              fieldSchema = fieldSchema.min(
                fieldRules.min_length,
                `Must be at least ${fieldRules.min_length} characters`
              );
            }
            if (fieldRules.max_length) {
              fieldSchema = fieldSchema.max(
                fieldRules.max_length,
                `Must be no more than ${fieldRules.max_length} characters`
              );
            }
            if (fieldRules.email) {
              fieldSchema = fieldSchema.email('Must be a valid email address');
            }
            if (fieldRules.pattern) {
              fieldSchema = fieldSchema.matches(
                new RegExp(fieldRules.pattern),
                fieldRules.error_message || 'Does not match the required pattern'
              );
            }
            break;
          
          case 'number':
            fieldSchema = yup.number().typeError('Must be a number');
            if (fieldRules.min !== undefined) {
              fieldSchema = fieldSchema.min(fieldRules.min, `Must be at least ${fieldRules.min}`);
            }
            if (fieldRules.max !== undefined) {
              fieldSchema = fieldSchema.max(fieldRules.max, `Must be no more than ${fieldRules.max}`);
            }
            if (fieldRules.integer) {
              fieldSchema = fieldSchema.integer('Must be a whole number');
            }
            break;
          
          case 'date':
            fieldSchema = yup.date().typeError('Must be a valid date');
            if (fieldRules.min_date) {
              const minDate = new Date(fieldRules.min_date);
              fieldSchema = fieldSchema.min(minDate, `Date must be on or after ${minDate.toISOString().split('T')[0]}`);
            }
            if (fieldRules.max_date) {
              const maxDate = new Date(fieldRules.max_date);
              fieldSchema = fieldSchema.max(maxDate, `Date must be on or before ${maxDate.toISOString().split('T')[0]}`);
            }
            if (fieldRules.future) {
              const today = new Date();
              today.setHours(0, 0, 0, 0);
              fieldSchema = fieldSchema.min(today, 'Date must be in the future');
            }
            if (fieldRules.past) {
              const today = new Date();
              today.setHours(0, 0, 0, 0);
              fieldSchema = fieldSchema.max(today, 'Date must be in the past');
            }
            break;
          
          case 'select':
            fieldSchema = yup.string();
            if (field.options && field.options.length > 0) {
              fieldSchema = fieldSchema.oneOf(
                field.options,
                `Must be one of: ${field.options.join(', ')}`
              );
            }
            break;
          
          case 'boolean':
          case 'checkbox':
            fieldSchema = yup.boolean();
            break;
          
          default:
            fieldSchema = yup.string();
        }

        // Add required validation
        if (field.required) {
          fieldSchema = fieldSchema.required('This field is required');
        }

        schemaObj[fieldId] = fieldSchema;
      });

      setValidationSchema(yup.object().shape(schemaObj));
    } catch (error) {
      console.error("Error building validation schema:", error);
      setFormError(`Failed to build form: ${error.message}`);
    }
  }, [formDefinition]);

  // Initialize Formik
  const formik = useFormik({
    initialValues: initialValues,
    validationSchema: validationSchema,
    enableReinitialize: true,
    onSubmit: async (values) => {
      if (onSubmit) {
        try {
          await onSubmit(values);
        } catch (error) {
          setFormError(`Submission failed: ${error.message}`);
        }
      }
    },
  });

  // Handle form cancel
  const handleCancel = () => {
    formik.resetForm();
    if (onCancel) {
      onCancel();
    }
  };

  if (!formDefinition) {
    return <Typography color="error">No form definition provided</Typography>;
  }

  return (
    <Card>
      <CardHeader 
        title={formDefinition.name || "Form"} 
        subheader={formDefinition.description} 
      />
      <Divider />
      <CardContent>
        {formError && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {formError}
          </Alert>
        )}
        
        <form onSubmit={formik.handleSubmit} noValidate>
          <Grid container spacing={3}>
            {formFields.map((field) => (
              <Grid item xs={12} md={field.fullWidth ? 12 : 6} key={field.id}>
                {renderField(field, formik, isReadOnly)}
              </Grid>
            ))}
            
            {!isReadOnly && (
              <Grid item xs={12}>
                <Box display="flex" justifyContent="flex-end" mt={2}>
                  <Button
                    onClick={handleCancel}
                    sx={{ mr: 2 }}
                    disabled={isLoading}
                  >
                    {cancelLabel}
                  </Button>
                  <Button
                    type="submit"
                    variant="contained"
                    color="primary"
                    disabled={isLoading}
                    startIcon={isLoading ? <CircularProgress size={20} /> : null}
                  >
                    {submitLabel}
                  </Button>
                </Box>
              </Grid>
            )}
          </Grid>
        </form>
      </CardContent>
    </Card>
  );
};

/**
 * Helper function to render the appropriate form field based on its type
 */
const renderField = (field, formik, isReadOnly) => {
  const {
    id,
    label,
    type,
    description,
    placeholder,
    options = [],
    required,
    fullWidth = true,
  } = field;

  const fieldProps = {
    id: id,
    name: id,
    label: label,
    fullWidth: fullWidth,
    value: formik.values[id] !== undefined ? formik.values[id] : '',
    onChange: formik.handleChange,
    onBlur: formik.handleBlur,
    error: formik.touched[id] && Boolean(formik.errors[id]),
    helperText: (formik.touched[id] && formik.errors[id]) || description,
    placeholder: placeholder,
    required: required,
    disabled: isReadOnly,
    margin: "normal",
    variant: "outlined",
  };

  switch (type) {
    case 'textarea':
      return (
        <TextField
          {...fieldProps}
          multiline
          rows={4}
        />
      );

    case 'number':
      return (
        <TextField
          {...fieldProps}
          type="number"
          inputProps={{ step: "any" }}
        />
      );

    case 'date':
      return (
        <LocalizationProvider dateAdapter={AdapterDateFns}>
          <DatePicker
            label={label}
            value={formik.values[id] ? new Date(formik.values[id]) : null}
            onChange={(date) => formik.setFieldValue(id, date)}
            slotProps={{
              textField: {
                ...fieldProps,
                onBlur: formik.handleBlur,
                error: formik.touched[id] && Boolean(formik.errors[id]),
                helperText: (formik.touched[id] && formik.errors[id]) || description,
              },
            }}
            disabled={isReadOnly}
          />
        </LocalizationProvider>
      );

    case 'select':
      return (
        <FormControl
          fullWidth={fullWidth}
          error={formik.touched[id] && Boolean(formik.errors[id])}
          margin="normal"
          variant="outlined"
          disabled={isReadOnly}
        >
          <InputLabel id={`${id}-label`} required={required}>
            {label}
          </InputLabel>
          <Select
            labelId={`${id}-label`}
            id={id}
            name={id}
            value={formik.values[id] || ''}
            onChange={formik.handleChange}
            onBlur={formik.handleBlur}
            label={label}
          >
            <MenuItem value="">
              <em>None</em>
            </MenuItem>
            {options.map((option) => (
              <MenuItem key={option} value={option}>
                {option}
              </MenuItem>
            ))}
          </Select>
          {(formik.touched[id] && formik.errors[id]) ? (
            <FormHelperText error>{formik.errors[id]}</FormHelperText>
          ) : description ? (
            <FormHelperText>{description}</FormHelperText>
          ) : null}
        </FormControl>
      );

    case 'boolean':
    case 'checkbox':
      return (
        <FormControl
          fullWidth={fullWidth}
          error={formik.touched[id] && Boolean(formik.errors[id])}
          margin="normal"
          disabled={isReadOnly}
        >
          <FormControlLabel
            control={
              <Switch
                id={id}
                name={id}
                checked={Boolean(formik.values[id])}
                onChange={formik.handleChange}
                onBlur={formik.handleBlur}
                disabled={isReadOnly}
              />
            }
            label={label}
          />
          {(formik.touched[id] && formik.errors[id]) ? (
            <FormHelperText error>{formik.errors[id]}</FormHelperText>
          ) : description ? (
            <FormHelperText>{description}</FormHelperText>
          ) : null}
        </FormControl>
      );

    case 'text':
    default:
      return <TextField {...fieldProps} />;
  }
};

export default DynamicForm; 