// types/dashboard.ts

export interface BulkEmailSenderProps {
  periodId: number;
  onClose: () => void;
}

export interface User {
  id: number;
  name: string;
  is_admin: boolean;
  is_super_admin: boolean;
}

export interface TeachingPeriod {
  id: number;
  name: string;
}

export interface DashboardMetrics {
  totalStudents: number;
  totalReports: number;
  reportCompletion: number;
  currentGroups: GroupProgress[];
  coachSummaries?: CoachSummary[];
}

export interface GroupProgress {
  name: string;
  count: number;
  reports_completed: number;
}

export interface CoachSummary {
  id: number;
  name: string;
  total_assigned: number;
  reports_completed: number;
}

export interface ProgrammePlayer {
  id: number;
  student_name: string;
  group_name: string;
  report_submitted: boolean;
  report_id?: number;
  can_edit: boolean;
}

// New interfaces for templates
export interface TemplateField {
  id?: number;
  name: string;
  description?: string;
  fieldType: 'text' | 'number' | 'select' | 'textarea' | 'rating';
  isRequired: boolean;
  order: number;
  options?: {
    options?: string[];
    min?: number;
    max?: number;
  };
}

export interface TemplateSection {
  id?: number;
  name: string;
  order: number;
  fields: TemplateField[];
}

export interface ReportTemplate {
  id?: number;
  name: string;
  description?: string;
  sections: TemplateSection[];
  isActive: boolean;
  emailSubjectTemplate?: string;
  emailBodyTemplate?: string;
}

export interface GroupTemplate {
  groupId: number;
  templateId: number;
  groupName: string;
  templateName: string;
  isActive: boolean;
}

export interface ReportContent {
  [sectionName: string]: {
    [fieldName: string]: string | number;
  };
}

export enum FieldType {
  TEXT = 'text',
  NUMBER = 'number',
  SELECT = 'select',
  TEXTAREA = 'textarea',
  RATING = 'rating'
}