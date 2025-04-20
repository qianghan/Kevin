export interface Profile {
  id: string;
  user_id: string;
  personal_info: PersonalInfo;
  education: Education[];
  experience: Experience[];
  skills: Skill[];
  projects: Project[];
  certifications: Certification[];
  languages: Language[];
  interests: Interest[];
  references: Reference[];
  metadata: ProfileMetadata;
}

export interface PersonalInfo {
  name: string;
  email: string;
  phone: string;
  location: string;
  website: string;
  summary: string;
  photo_url?: string;
}

export interface Education {
  institution: string;
  degree: string;
  field: string;
  start_date: string;
  end_date: string;
  gpa?: number;
  description?: string;
}

export interface Experience {
  company: string;
  position: string;
  start_date: string;
  end_date: string;
  description: string;
  achievements: string[];
}

export interface Skill {
  name: string;
  level: string;
  category: string;
  description?: string;
}

export interface Project {
  name: string;
  description: string;
  start_date: string;
  end_date: string;
  technologies: string[];
  url?: string;
}

export interface Certification {
  name: string;
  issuer: string;
  date: string;
  url?: string;
}

export interface Language {
  name: string;
  level: string;
}

export interface Interest {
  name: string;
  description?: string;
}

export interface Reference {
  name: string;
  position: string;
  company: string;
  email: string;
  phone: string;
}

export interface ProfileMetadata {
  created_at: string;
  updated_at: string;
  version: number;
  status: string;
} 