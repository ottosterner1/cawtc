import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';

interface Group {
  id: number;
  name: string;
}

interface FieldOption {
  id: number;
  name: string;
  description?: string;
  fieldType: 'text' | 'number' | 'select' | 'textarea' | 'rating' | 'progress';
  isRequired: boolean;
  options?: {
    min?: number;
    max?: number;
    options?: string[];
  };
  order: number;
}

interface Section {
  id: number;
  name: string;
  order: number;
  fields: FieldOption[];
}

interface Template {
  id: number;
  name: string;
  description: string;
  sections: Section[];
}

interface DynamicReportFormProps {
  template: Template;
  studentName: string;
  groupName: string;
  initialData?: Record<string, Record<string, any>>;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  onCancel: () => void;
  isSubmitting?: boolean;
}

interface ProgressOptionsProps {
  value: string;
  onChange: (value: string) => void;
  error?: boolean;
  isRequired?: boolean;
  name: string;
}

const ProgressOptions: React.FC<ProgressOptionsProps> = ({ 
  value, 
  onChange, 
  isRequired,
  name 
}) => {
  const options = ['Yes', 'Nearly', 'Not Yet'];

  return (
    <div className="flex space-x-6 items-center">
      {options.map((option) => (
        <label
          key={option}
          className={`flex items-center space-x-2 cursor-pointer ${
            value === option ? 'text-blue-600' : 'text-gray-700'
          }`}
        >
          <input
            type="radio"
            name={name}
            value={option}
            checked={value === option}
            onChange={() => onChange(option)}
            className="w-4 h-4 text-blue-600 focus:ring-blue-500"
            required={isRequired && !value}
          />
          <span className="text-sm">{option}</span>
        </label>
      ))}
    </div>
  );
};

const DynamicReportForm: React.FC<DynamicReportFormProps> = ({
  template,
  studentName,
  groupName,
  initialData,
  onSubmit,
  onCancel,
  isSubmitting = false
}) => {
  const [formData, setFormData] = useState<Record<string, Record<string, any>>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [touched, setTouched] = useState<Record<string, Record<string, boolean>>>({});
  const [groups, setGroups] = useState<Group[]>([]);
  const [recommendedGroupId, setRecommendedGroupId] = useState<number | string>('');

  useEffect(() => {
    const fetchGroups = async () => {
      try {
        const response = await fetch('/api/groups');
        if (response.ok) {
          const data = await response.json();
          setGroups(data);
        }
      } catch (error) {
        console.error('Error fetching groups:', error);
      }
    };
    fetchGroups();
  }, []);

  useEffect(() => {
    if (initialData) {
      setFormData(initialData);
      if ('recommendedGroupId' in initialData && typeof initialData.recommendedGroupId === 'number') {
        setRecommendedGroupId(initialData.recommendedGroupId);
      } else {
        setRecommendedGroupId('');
      }
      const touchedFields: Record<string, Record<string, boolean>> = {};
      template.sections.forEach(section => {
        touchedFields[section.name] = {};
        section.fields.forEach(field => {
          touchedFields[section.name][field.name] = true;
        });
      });
      setTouched(touchedFields);
    } else {
      const initialFormData: Record<string, Record<string, any>> = {};
      template.sections.forEach(section => {
        initialFormData[section.name] = {};
        section.fields.forEach(field => {
          initialFormData[section.name][field.name] = '';
        });
      });
      setFormData(initialFormData);
    }
  }, [initialData, template]);

  const handleFieldChange = (sectionName: string, fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [sectionName]: {
        ...prev[sectionName],
        [fieldName]: value
      }
    }));

    setTouched(prev => ({
      ...prev,
      [sectionName]: {
        ...prev[sectionName],
        [fieldName]: true
      }
    }));

    setErrors(prev => prev.filter(error => !error.includes(fieldName)));
  };

  const validateField = (section: Section, field: FieldOption): string | null => {
    const value = formData[section.name]?.[field.name];
    
    if (field.isRequired && (!value || value.toString().trim() === '')) {
      return `${field.name} is required`;
    }

    switch (field.fieldType) {
      case 'number':
        if (value && isNaN(Number(value))) {
          return `${field.name} must be a valid number`;
        }
        if (field.options?.min !== undefined && Number(value) < field.options.min) {
          return `${field.name} must be at least ${field.options.min}`;
        }
        if (field.options?.max !== undefined && Number(value) > field.options.max) {
          return `${field.name} must be no more than ${field.options.max}`;
        }
        break;
      case 'rating':
        if (value && (isNaN(Number(value)) || Number(value) < 1 || Number(value) > 5)) {
          return `${field.name} must be between 1 and 5`;
        }
        break;
    }

    return null;
  };

  const validateForm = (): boolean => {
    const newErrors: string[] = [];

    template.sections.forEach(section => {
      section.fields.forEach(field => {
        const error = validateField(section, field);
        if (error) {
          newErrors.push(error);
        }
      });
    });

    if (!recommendedGroupId) {
      newErrors.push('Please select a recommended group');
    }

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      const submitData = {
        content: formData,
        recommendedGroupId: Number(recommendedGroupId),
        template_id: template.id
      };

      await onSubmit(submitData);
    } catch (error) {
      setErrors(prev => [...prev, 'Failed to submit report. Please try again.']);
      console.error('Submit error:', error);
    }
  };

  const renderField = (section: Section, field: FieldOption) => {
    const value = formData[section.name]?.[field.name] || '';
    const isTouched = touched[section.name]?.[field.name];
    const error = isTouched ? validateField(section, field) : null;

    if (field.fieldType === 'progress') {
      return (
        <div className="flex justify-between items-center py-2">
          <div className="flex-1">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 inline ml-2">
                {field.description}
              </p>
            )}
          </div>
          <div className="flex-1">
            <ProgressOptions
              value={value}
              onChange={(newValue) => handleFieldChange(section.name, field.name, newValue)}
              error={!!error}
              isRequired={field.isRequired}
              name={`progress_${section.id}_${field.id}`}
            />
          </div>
        </div>
      );
    }

    const commonProps = {
      id: `field_${section.id}_${field.id}`,
      value,
      onChange: (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => 
        handleFieldChange(section.name, field.name, e.target.value),
      className: `w-full p-2 border rounded ${error ? 'border-red-500' : 'border-gray-300'} 
                 focus:outline-none focus:ring-2 focus:ring-blue-500`,
      required: field.isRequired
    };

    switch (field.fieldType) {
      case 'text':
        return (
          <div className="space-y-2">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="block text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 mb-1">{field.description}</p>
            )}
            <input type="text" {...commonProps} />
          </div>
        );
      
      case 'textarea':
        return (
          <div className="space-y-2">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="block text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 mb-1">{field.description}</p>
            )}
            <textarea {...commonProps} className={`${commonProps.className} h-24`} />
          </div>
        );
      
      case 'number':
        return (
          <div className="space-y-2">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="block text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 mb-1">{field.description}</p>
            )}
            <input
              type="number"
              min={field.options?.min}
              max={field.options?.max}
              {...commonProps}
            />
          </div>
        );
      
      case 'select':
        return (
          <div className="space-y-2">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="block text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 mb-1">{field.description}</p>
            )}
            <select {...commonProps}>
              <option value="">Select an option</option>
              {field.options?.options?.map((option) => (
                <option key={option} value={option}>{option}</option>
              ))}
            </select>
          </div>
        );
      
      case 'rating':
        return (
          <div className="space-y-2">
            <label 
              htmlFor={`field_${section.id}_${field.id}`}
              className="block text-sm font-medium text-gray-700"
            >
              {field.name}
              {field.isRequired && <span className="text-red-500 ml-1">*</span>}
            </label>
            {field.description && (
              <p className="text-sm text-gray-500 mb-1">{field.description}</p>
            )}
            <select {...commonProps}>
              <option value="">Select rating</option>
              {[1, 2, 3, 4, 5].map((rating) => (
                <option key={rating} value={rating}>
                  {rating} - {['Poor', 'Below Average', 'Average', 'Good', 'Excellent'][rating - 1]}
                </option>
              ))}
            </select>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>{initialData ? 'Edit Report' : 'Create Report'}</CardTitle>
        <div className="text-sm text-gray-600">
          <div>Student: {studentName}</div>
          <div>Current Group: {groupName}</div>
        </div>
      </CardHeader>
      <CardContent>
        {errors.length > 0 && (
          <Alert variant="destructive" className="mb-4">
            <AlertDescription>
              <ul className="list-disc list-inside">
                {errors.map((error, index) => (
                  <li key={index}>{error}</li>
                ))}
              </ul>
            </AlertDescription>
          </Alert>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          {template.sections
            .sort((a, b) => a.order - b.order)
            .map((section) => (
              <div key={section.id} className="space-y-4">
                <h3 className="font-semibold text-lg border-b pb-2">{section.name}</h3>
                <div className="space-y-4">
                  {section.fields
                    .sort((a, b) => a.order - b.order)
                    .map((field) => (
                      <div key={field.id}>
                        {renderField(section, field)}
                        {touched[section.name]?.[field.name] && 
                         validateField(section, field) && (
                          <p className="text-sm text-red-500 mt-1">
                            {validateField(section, field)}
                          </p>
                        )}
                      </div>
                    ))}
                </div>
              </div>
            ))}

          <div className="space-y-2">
            <label 
              htmlFor="recommendedGroup"
              className="block text-sm font-medium text-gray-700"
            >
              Recommended Group<span className="text-red-500 ml-1">*</span>
            </label>
            <select
              id="recommendedGroup"
              value={recommendedGroupId}
              onChange={(e) => setRecommendedGroupId(Number(e.target.value) || '')}
              className="w-full p-2 border rounded border-gray-300 focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            >
              <option value="">Select a group</option>
              {groups.map((group) => (
                <option key={group.id} value={group.id}>
                  {group.name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex justify-end space-x-4 mt-6">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 border rounded-md hover:bg-gray-50"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 
                       disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isSubmitting}
            >
              {isSubmitting ? (
                <span className="flex items-center">
                  <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Saving...
                </span>
              ) : initialData ? 'Update Report' : 'Save Report'}
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default DynamicReportForm;