import React, { useState, useEffect } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '../ui/card';
import { Alert, AlertDescription } from '../ui/alert';
import { ReportTemplate, TemplateSection, TemplateField } from '../../types/dashboard';

interface TemplateEditorProps {
  template?: ReportTemplate;
  onSave: (template: ReportTemplate) => void;
  onCancel: () => void;
}

const TemplateEditor: React.FC<TemplateEditorProps> = ({ template, onSave, onCancel }) => {
  const [name, setName] = useState(template?.name || '');
  const [description, setDescription] = useState(template?.description || '');
  const [sections, setSections] = useState<TemplateSection[]>(template?.sections || []);
  const [emailSubject, setEmailSubject] = useState(template?.emailSubjectTemplate || '');
  const [emailBody, setEmailBody] = useState(template?.emailBodyTemplate || '');

  const addSection = () => {
    setSections([...sections, {
      name: '',
      order: sections.length,
      fields: []
    }]);
  };

  const addField = (sectionIndex: number) => {
    const newSections = [...sections];
    newSections[sectionIndex].fields.push({
      name: '',
      fieldType: 'text',
      isRequired: true,
      order: newSections[sectionIndex].fields.length
    });
    setSections(newSections);
  };

  const updateField = (sectionIndex: number, fieldIndex: number, updates: Partial<TemplateField>) => {
    const newSections = [...sections];
    newSections[sectionIndex].fields[fieldIndex] = {
      ...newSections[sectionIndex].fields[fieldIndex],
      ...updates
    };
    setSections(newSections);
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onSave({
      id: template?.id,
      name,
      description,
      sections,
      isActive: true,
      emailSubjectTemplate: emailSubject,
      emailBodyTemplate: emailBody
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div>
        <label className="block text-sm font-medium text-gray-700">Template Name</label>
        <input
          type="text"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          required
        />
      </div>

      <div>
        <label className="block text-sm font-medium text-gray-700">Description</label>
        <textarea
          value={description}
          onChange={(e) => setDescription(e.target.value)}
          className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
          rows={3}
        />
      </div>

      <div className="space-y-4">
        <h3 className="text-lg font-medium">Sections</h3>
        {sections.map((section, sectionIndex) => (
          <div key={sectionIndex} className="p-4 border rounded-md">
            <input
              type="text"
              value={section.name}
              onChange={(e) => {
                const newSections = [...sections];
                newSections[sectionIndex].name = e.target.value;
                setSections(newSections);
              }}
              placeholder="Section Name"
              className="block w-full mb-4"
            />

            <div className="space-y-4">
              {section.fields.map((field, fieldIndex) => (
                <div key={fieldIndex} className="flex gap-4">
                  <input
                    type="text"
                    value={field.name}
                    onChange={(e) => updateField(sectionIndex, fieldIndex, { name: e.target.value })}
                    placeholder="Field Name"
                    className="flex-1"
                  />
                  <select
                    value={field.fieldType}
                    onChange={(e) => updateField(sectionIndex, fieldIndex, { fieldType: e.target.value as any })}
                    className="w-32"
                  >
                    <option value="text">Text</option>
                    <option value="number">Number</option>
                    <option value="select">Select</option>
                    <option value="textarea">Text Area</option>
                    <option value="rating">Rating</option>
                  </select>
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={field.isRequired}
                      onChange={(e) => updateField(sectionIndex, fieldIndex, { isRequired: e.target.checked })}
                      className="mr-2"
                    />
                    Required
                  </label>
                </div>
              ))}
              <button
                type="button"
                onClick={() => addField(sectionIndex)}
                className="text-sm text-blue-500"
              >
                + Add Field
              </button>
            </div>
          </div>
        ))}
        <button
          type="button"
          onClick={addSection}
          className="text-blue-500"
        >
          + Add Section
        </button>
      </div>

      <div>
        <h3 className="text-lg font-medium mb-4">Email Templates</h3>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Email Subject Template</label>
            <input
              type="text"
              value={emailSubject}
              onChange={(e) => setEmailSubject(e.target.value)}
              className="mt-1 block w-full"
              placeholder="e.g., Tennis Report for {{ student_name }}"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">Email Body Template</label>
            <textarea
              value={emailBody}
              onChange={(e) => setEmailBody(e.target.value)}
              className="mt-1 block w-full"
              rows={5}
              placeholder="Available variables: {{ student_name }}, {{ group_name }}, {{ coach_name }}, {{ date }}"
            />
          </div>
        </div>
      </div>

      <div className="flex justify-end space-x-4">
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

const TemplateManager: React.FC = () => {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [editingTemplate, setEditingTemplate] = useState<ReportTemplate | undefined>();
  const [error, setError] = useState<string>('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      const response = await fetch('/api/report-templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      setError('Failed to load templates');
    }
  };

  const handleSaveTemplate = async (template: ReportTemplate) => {
    try {
      const method = template.id ? 'PUT' : 'POST';
      const url = template.id ? `/api/report-templates/${template.id}` : '/api/report-templates';
      
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(template),
      });
      
      if (!response.ok) throw new Error('Failed to save template');
      
      setEditingTemplate(undefined);
      fetchTemplates();
    } catch (err) {
      setError('Failed to save template');
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      {editingTemplate ? (
        <Card>
          <CardHeader>
            <CardTitle>{editingTemplate.id ? 'Edit Template' : 'New Template'}</CardTitle>
          </CardHeader>
          <CardContent>
            <TemplateEditor
              template={editingTemplate}
              onSave={handleSaveTemplate}
              onCancel={() => setEditingTemplate(undefined)}
            />
          </CardContent>
        </Card>
      ) : (
        <>
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold">Report Templates</h2>
            <button
              onClick={() => setEditingTemplate({
                name: '',
                description: '',
                sections: [],
                isActive: true,
                emailSubjectTemplate: '',
                emailBodyTemplate: ''
              } as ReportTemplate)}
              className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600"
            >
              Create Template
            </button>
          </div>

          <div className="grid grid-cols-1 gap-6">
            {templates.map((template) => (
              <Card key={template.id} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <CardTitle className="flex justify-between items-center">
                    <span>{template.name}</span>
                    <button
                      onClick={() => setEditingTemplate(template)}
                      className="text-sm text-blue-500 hover:text-blue-600"
                    >
                      Edit
                    </button>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-gray-600 mb-4">{template.description}</p>
                  <div className="space-y-4">
                    {template.sections.map((section) => (
                      <div key={section.id} className="border-t pt-4">
                        <h4 className="font-medium mb-2">{section.name}</h4>
                        <ul className="list-disc list-inside pl-4">
                          {section.fields.map((field) => (
                            <li key={field.id} className="text-sm text-gray-600">
                              {field.name} ({field.fieldType})
                              {field.isRequired && ' *'}
                            </li>
                          ))}
                        </ul>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </>
      )}
    </div>
  );
};

export default TemplateManager;