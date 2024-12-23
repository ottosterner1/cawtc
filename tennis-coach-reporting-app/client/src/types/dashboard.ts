// src/types/dashboard.ts

export interface Group {
  id: number;
  name: string;
  description?: string;
}

export interface TemplateField {
  id?: number;
  name: string;
  description?: string;
  fieldType: 'text' | 'textarea' | 'rating' | 'select' | 'progress';
  isRequired: boolean;
  order: number;
  options?: {
    min?: number;
    max?: number;
    options?: string[];
  } | null;
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
  assignedGroups: Group[];
}

export interface GroupTemplate {
  templateId: number;
  groupId: number;
  groupName: string;
  templateName: string;
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