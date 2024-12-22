import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';

interface FieldOption {
  name: string;
  fieldType: 'text' | 'number' | 'select' | 'textarea' | 'rating';
  isRequired: boolean;
  options?: any;
}

interface Section {
  name: string;
  fields: FieldOption[];
}

interface Template {
  id?: number;
  name: string;
  description: string;
  sections: Section[];
}

interface DynamicReportFormProps {
  template: Template;
  studentName: string;
  groupName: string;
  onSubmit: (data: Record<string, any>) => Promise<void>;
  onCancel: () => void;
}

const DynamicReportForm: React.FC<DynamicReportFormProps> = ({
  template,
  studentName,
  groupName,
  onSubmit,
  onCancel
}) => {
  const [formData, setFormData] = useState<Record<string, Record<string, any>>>({});
  const [errors, setErrors] = useState<string[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleFieldChange = (sectionName: string, fieldName: string, value: any) => {
    setFormData(prev => ({
      ...prev,
      [sectionName]: {
        ...prev[sectionName],
        [fieldName]: value
      }
    }));
  };

  const validateForm = () => {
    const newErrors: string[] = [];

    template.sections.forEach(section => {
      section.fields.forEach(field => {
        const value = formData[section.name]?.[field.name];
        if (field.isRequired && !value) {
          newErrors.push(`${field.name} is required`);
        }
      });
    });

    setErrors(newErrors);
    return newErrors.length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onSubmit(formData);
    } catch (error) {
      setErrors(['Failed to submit report. Please try again.']);
    } finally {
      setIsSubmitting(false);
    }
  };

  const renderField = (section: Section, field: FieldOption) => {
    const value = formData[section.name]?.[field.name] || '';

    switch (field.fieldType) {
      case 'text':
        return (
          <input
            type="text"
            value={value}
            onChange={(e) => handleFieldChange(section.name, field.name, e.target.value)}
            className="w-full p-2 border rounded"
            required={field.isRequired}
          />
        );
      
      case 'textarea':
        return (
          <textarea
            value={value}
            onChange={(e) => handleFieldChange(section.name, field.name, e.target.value)}
            className="w-full p-2 border rounded h-24"
            required={field.isRequired}
          />
        );
      
      case 'number':
        return (
          <input
            type="number"
            value={value}
            onChange={(e) => handleFieldChange(section.name, field.name, e.target.value)}
            className="w-full p-2 border rounded"
            required={field.isRequired}
          />
        );
      
      case 'select':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(section.name, field.name, e.target.value)}
            className="w-full p-2 border rounded"
            required={field.isRequired}
          >
            <option value="">Select an option</option>
            {field.options?.options?.map((option: string) => (
              <option key={option} value={option}>
                {option}
              </option>
            ))}
          </select>
        );
      
      case 'rating':
        return (
          <select
            value={value}
            onChange={(e) => handleFieldChange(section.name, field.name, e.target.value)}
            className="w-full p-2 border rounded"
            required={field.isRequired}
          >
            <option value="">Select rating</option>
            {[1, 2, 3, 4, 5].map((rating) => (
              <option key={rating} value={rating}>
                {rating} - {['Poor', 'Below Average', 'Average', 'Good', 'Excellent'][rating - 1]}
              </option>
            ))}
          </select>
        );
      
      default:
        return null;
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Create Report</CardTitle>
        <div className="text-sm text-gray-600">
          <div>Student: {studentName}</div>
          <div>Group: {groupName}</div>
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
          {template.sections.map((section) => (
            <div key={section.name} className="space-y-4">
              <h3 className="font-semibold text-lg border-b pb-2">{section.name}</h3>
              <div className="space-y-4">
                {section.fields.map((field) => (
                  <div key={field.name} className="space-y-2">
                    <label className="block text-sm font-medium text-gray-700">
                      {field.name}
                      {field.isRequired && <span className="text-red-500 ml-1">*</span>}
                    </label>
                    {renderField(section, field)}
                  </div>
                ))}
              </div>
            </div>
          ))}

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
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:opacity-50"
              disabled={isSubmitting}
            >
              {isSubmitting ? 'Saving...' : 'Save Report'}
            </button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
};

export default DynamicReportForm;