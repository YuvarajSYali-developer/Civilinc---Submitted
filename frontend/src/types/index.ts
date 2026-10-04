export type Role = 'commissioner' | 'engineer' | 'coordinator' | 'citizen'
export type Priority = 'low' | 'medium' | 'high' | 'critical'
export type ComplaintStatus = 'pending' | 'under_review' | 'assigned' | 'in_progress' | 'resolved' | 'closed' | 'rejected' | 'escalated'
export type ProjectStatus = 'planning' | 'tendering' | 'in_progress' | 'on_hold' | 'completed' | 'cancelled'
export type RiskCategory = 'low' | 'medium' | 'high' | 'critical'

export interface User {
  id: string; email: string; full_name: string; role: Role
  department_id?: string; employee_id?: string; designation?: string
  ward_number?: string; zone?: string; avatar_url?: string
  is_active: boolean; is_verified: boolean; created_at: string
}

export interface TokenResponse {
  access_token: string; refresh_token: string
  token_type: string; expires_in: number
  user_id: string; role: Role; full_name: string
}

export interface Department {
  id: string; name: string; code: string; description?: string
  email?: string; phone?: string; status: string
  annual_budget?: number; budget_utilized: number; sla_hours: number
  total_complaints: number; resolved_complaints: number
  total_projects: number; active_projects: number
  complaint_categories?: string[]; created_at: string
}

export interface Complaint {
  id: string; complaint_number: string; title: string; description: string
  category: string; sub_category?: string; status: ComplaintStatus; priority: Priority
  address?: string; ward_number?: string; zone?: string
  latitude?: number; longitude?: number
  citizen_id: string; department_id?: string; assigned_officer_id?: string
  ai_predicted_category?: string; ai_predicted_priority?: string
  ai_predicted_resolution_days?: number; ai_confidence_score?: number
  ai_processed?: boolean
  sla_breached: boolean; sla_due_at?: string
  citizen_rating?: number; source: string; escalation_level: number
  created_at: string; updated_at: string
}

export interface ComplaintHistory {
  id: string; action: string
  previous_status?: string; new_status?: string
  previous_priority?: string; new_priority?: string
  comment?: string; created_at: string
}

export interface Project {
  id: string; project_number: string; title: string; description?: string
  category: string; status: ProjectStatus; phase?: string
  completion_percentage: number
  planned_start_date?: string; planned_end_date?: string
  actual_start_date?: string; estimated_cost: number
  approved_budget?: number; actual_cost: number; budget_utilized_pct: number
  department_id: string; project_manager_id?: string
  ward_number?: string; zone?: string
  delay_probability?: number; overrun_probability?: number
  risk_score?: number; risk_category?: RiskCategory
  contractor_name?: string; is_public: boolean
  created_at: string; updated_at: string
}

export interface Notification {
  id: string; title: string; message: string
  notification_type: string; is_read: boolean; read_at?: string
  action_url?: string; icon?: string; priority: string
  entity_type?: string; entity_id?: string; created_at: string
}

export interface WardRisk {
  ward_number: string; risk_score: number; risk_category: RiskCategory
  total_complaints: number; sla_breach_rate: number; avg_delay_prob: number
}

export interface PaginatedResponse<T> {
  items: T[]; total: number; page: number
  page_size: number; pages: number; has_next: boolean; has_prev: boolean
}

export interface AnalyticsOverview {
  complaints: {
    total: number; pending: number; resolved: number
    critical: number; sla_breached: number; resolution_rate: number
  }
  projects: {
    total: number; active: number; at_risk: number
    total_budget: number; actual_cost: number; budget_utilization_pct: number
  }
}

export interface AITriageResult {
  category: string; department: string; priority: Priority
  resolution_days: number; cluster_id: number; confidence: number; sla_hours: number
}

export interface ForumThread {
  id: string; title: string; body: string; category: string
  author_id: string; department_id?: string
  is_pinned: boolean; is_locked: boolean; is_announcement: boolean
  view_count: number; comment_count: number; upvotes: number
  tags?: string[]; created_at: string
}
