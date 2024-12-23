import React, { useState, useEffect } from 'react';
import { Card, CardContent } from '../../components/ui/card';
import { Alert, AlertDescription } from '../../components/ui/alert';
import type { ReportTemplate, TemplateSection, TemplateField } from '../../types/dashboard';

interface TemplateEditorProps {
  template?: ReportTemplate;
  onSave: (template: ReportTemplate) => void;
  onCancel: () => void;
}

// Define available field types
const FIELD_TYPES = [
  { value: 'text', label: 'Short Text' },
  { value: 'textarea', label: 'Long Text' },
  { value: 'rating', label: 'Rating (1-5)' },
  { value: 'select', label: 'Multiple Choice' },
  { value: 'progress', label: 'Progress Scale (Yes/Nearly/Not Yet)' }
];

const DEFAULT_OPTIONS = {
  rating: {
    min: 1,
    max: 5,
    options: ['Needs Development', 'Developing', 'Competent', 'Proficient', 'Excellent']
  },
  progress: {
    options: ['Yes', 'Nearly', 'Not Yet']
  }
};

const TemplateEditor: React.FC<TemplateEditorProps> = ({ template, onSave, onCancel }) => {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [sections, setSections] = useState<TemplateSection[]>(template?.sections || []);
  const [errors, setErrors] = useState<string[]>([]);
  const [selectedGroups, setSelectedGroups] = useState<number[]>(
    template?.assignedGroups?.map(g => g.id) || []
  );
  const [availableGroups, setAvailableGroups] = useState<Array<{ id: number, name: string }>>([]);

  useEffect(() => {
    // Fetch available groups
    const fetchGroups = async () => {
      try {
        const response = await fetch('/api/groups');
        if (!response.ok) throw new Error('Failed to fetch groups');
        const groups = await response.json();
        setAvailableGroups(groups);
      } catch (error) {
        console.error('Error fetching groups:', error);
      }
    };
    fetchGroups();
  }, []);

  const addSection = () => {
    setSections([...sections, {
      name: '',
      order: sections.length,
      fields: []
    }]);
  };

  const updateSection = (index: number, updates: Partial<TemplateSection>) => {
    const newSections = [...sections];
    newSections[index] = { ...newSections[index], ...updates };
    setSections(newSections);
  };

  const removeSection = (index: number) => {
    setSections(sections.filter((_, i) => i !== index));
  };

  const addField = (sectionIndex: number) => {
    const newSections = [...sections];
    newSections[sectionIndex].fields.push({
      name: '',
      fieldType: 'text',
      isRequired: true,
      order: newSections[sectionIndex].fields.length,
      options: null
    });
    setSections(newSections);
  };

  const updateField = (sectionIndex: number, fieldIndex: number, updates: Partial<TemplateField>) => {
    const newSections = [...sections];
    const field = newSections[sectionIndex].fields[fieldIndex];
  
    // If field type is changing, set default options
    if (updates.fieldType && FIELD_TYPES.some(type => type.value === updates.fieldType)) {
      updates.options = DEFAULT_OPTIONS[updates.fieldType as keyof typeof DEFAULT_OPTIONS] || null;
    }
  
    newSections[sectionIndex].fields[fieldIndex] = {
      ...field,
      ...updates
    };
    setSections(newSections);
  };

  const removeField = (sectionIndex: number, fieldIndex: number) => {
    const newSections = [...sections];
    newSections[sectionIndex].fields = newSections[sectionIndex].fields.filter((_, i) => i !== fieldIndex);
    setSections(newSections);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    const newErrors: string[] = [];
    if (!name.trim()) newErrors.push('Please provide a template name');
    if (sections.length === 0) newErrors.push('Add at least one section');
    if (selectedGroups.length === 0) newErrors.push('Please assign at least one group');
    
    sections.forEach((section, sIndex) => {
      if (!section.name.trim()) {
        newErrors.push(`Section ${sIndex + 1} needs a name`);
      }
      if (section.fields.length === 0) {
        newErrors.push(`Add at least one field in ${section.name || 'section ' + (sIndex + 1)}`);
      }
      section.fields.forEach((field, fIndex) => {
        if (!field.name.trim()) {
          newErrors.push(`Field ${fIndex + 1} in section ${section.name} needs a name`);
        }
      });
    });

    if (newErrors.length > 0) {
      setErrors(newErrors);
      return;
    }

    onSave({
      id: template?.id,
      name,
      description,
      sections: sections.map((section, sIndex) => ({
        ...section,
        order: sIndex,
        fields: section.fields.map((field, fIndex) => ({
          ...field,
          order: fIndex
        }))
      })),
      assignedGroups: selectedGroups.map(groupId => 
        availableGroups.find(g => g.id === groupId)!
      ),
      isActive: true
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {errors.length > 0 && (
        <Alert variant="destructive">
          <AlertDescription>
            <ul className="list-disc list-inside">
              {errors.map((error, index) => (
                <li key={index}>{error}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700">Template Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Description</label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            rows={2}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700">Assign Groups</label>
          <div className="mt-2 space-y-2">
            {availableGroups.map(group => (
              <label key={group.id} className="inline-flex items-center mr-4">
                <input
                  type="checkbox"
                  checked={selectedGroups.includes(group.id)}
                  onChange={(e) => {
                    setSelectedGroups(e.target.checked
                      ? [...selectedGroups, group.id]
                      : selectedGroups.filter(id => id !== group.id)
                    );
                  }}
                  className="rounded border-gray-300 text-blue-600 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                />
                <span className="ml-2">{group.name}</span>
              </label>
            ))}
          </div>
        </div>
      </div>

      <div className="space-y-4">
        <div className="flex justify-between items-center">
          <h3 className="text-lg font-medium">Assessment Sections</h3>
          <button
            type="button"
            onClick={addSection}
            className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
          >
            Add Section
          </button>
        </div>

        {sections.map((section, sectionIndex) => (
          <Card key={sectionIndex}>
            <CardContent>
              <div className="flex items-center justify-between">
                <input
                  type="text"
                  value={section.name}
                  onChange={(e) => updateSection(sectionIndex, { name: e.target.value })}
                  placeholder="Section Name"
                  className="flex-1 rounded-md border-gray-300"
                />
                <button
                  type="button"
                  onClick={() => removeSection(sectionIndex)}
                  className="ml-2 text-red-500 hover:text-red-600"
                >
                  Remove Section
                </button>
              </div>

              {section.fields.map((field, fieldIndex) => (
                <div key={fieldIndex} className="flex items-center gap-4">
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) => updateField(sectionIndex, fieldIndex, { name: e.target.value })}
                    placeholder="Field Name"
                    className="flex-1 rounded-md border-gray-300"
                  />
                  <select
                    value={field.fieldType}
                    onChange={(e) => updateField(sectionIndex, fieldIndex, { fieldType: e.target.value as 'text' | 'textarea' | 'rating' | 'select' | 'progress' })}
                    className="rounded-md border-gray-300"
                  >
                    {FIELD_TYPES.map(type => (
                      <option key={type.value} value={type.value}>{type.label}</option>
                    ))}
                  </select>
                  <label className="inline-flex items-center">
                    <input
                      type="checkbox"
                      checked={field.isRequired}
                      onChange={(e) => updateField(sectionIndex, fieldIndex, { isRequired: e.target.checked })}
                      className="rounded border-gray-300"
                    />
                    <span className="ml-2">Required</span>
                  </label>
                  <button
                    type="button"
                    onClick={() => removeField(sectionIndex, fieldIndex)}
                    className="text-red-500 hover:text-red-600"
                  >
                    Remove
                  </button>
                </div>
              ))}
              <button
                type="button"
                onClick={() => addField(sectionIndex)}
                className="text-sm text-blue-500 hover:text-blue-600"
              >
                + Add Field
              </button>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="flex justify-end space-x-4 mt-8">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 border rounded-md hover:bg-gray-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
        >
          Save Template
        </button>
      </div>
    </form>
  );
};

export default TemplateEditor;