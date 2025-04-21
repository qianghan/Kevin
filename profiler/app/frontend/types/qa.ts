export type QuestionCategory = 'professional' | 'education' | 'skills' | 'projects' | string;

export interface Question {
  id: string;
  text: string;
  category: QuestionCategory;
  importance?: number;
  profile_id: string;
  parent_question_id?: string;
  follow_up_questions: string[];
  created_at?: string;
  updated_at?: string;
  answer?: Answer;
}

export interface Answer {
  id?: string;
  question_id?: string;
  text: string;
  mediaType?: string;
  mediaUrl?: string;
  quality_score?: number;
  extracted_information?: Record<string, any>;
  submittedAt: string;
}

export interface Feedback {
  id?: string;
  question_id: string;
  feedback_text: string;
  rating?: number;
  submitted_at?: string;
}

export interface QASession {
  profile_id: string;
  exported_at: string;
  questions_count: number;
  answered_count: number;
  history: Array<Question & { answer?: Answer }>;
  analytics: QAAnalytics;
}

export interface QAAnalytics {
  total_questions: number;
  answered_questions: number;
  completion_rate: number;
  categories: Record<string, number>;
  average_answer_quality: number;
  excellent_answers: number;
  good_answers: number;
  adequate_answers: number;
  poor_answers: number;
} 