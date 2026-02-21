export type EntityStatus = "draft" | "published" | "cancelled" | "archived";

export interface Event {
  id: number;
  title: string;
  description: string;
  location: string;
  event_date: string | null;
  event_time: string | null;
  cover_image: string | null;
  ticket_link: string | null;
  status: EntityStatus;
  order: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface EventFormData {
  title: string;
  description: string;
  location: string;
  event_date: string;
  event_time: string;
  ticket_link: string;
  order: number;
}

export interface Course {
  id: number;
  title: string;
  description: string;
  detailed_description: string | null;
  schedule: string;
  image_desktop: string | null;
  image_mobile: string | null;
  cost: number;
  currency: string;
  status: EntityStatus;
  order: number;
  created_by: number | null;
  created_at: string;
  updated_at: string;
}

export interface CourseFormData {
  title: string;
  description: string;
  detailed_description: string;
  schedule: string;
  cost: string;
  currency: string;
  order: number;
}

export interface Contact {
  id: number;
  name: string;
  phone: string;
  email: string | null;
  message: string;
  source: string | null;
  is_processed: boolean;
  processed_by: number | null;
  created_at: string;
  processed_at: string | null;
}

export interface User {
  id: number;
  telegram_id: number;
  username: string | null;
  first_name: string | null;
  last_name: string | null;
  added_by: number | null;
  created_at: string;
}

export interface NewUserFormData {
  telegram_id: string;
  username: string;
  first_name: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
}
