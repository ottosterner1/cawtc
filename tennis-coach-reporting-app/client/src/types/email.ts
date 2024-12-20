// src/types/email.ts
  
  export interface BulkEmailFormData {
    teachingPeriod: number | null;
    templateId: number;
    bookingDate: string;
    bookingTime: string;
    bookingPassword: string;
  }