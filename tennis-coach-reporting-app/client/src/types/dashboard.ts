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
