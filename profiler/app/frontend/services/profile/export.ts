import { Profile } from '../../../types/profile';

export class ProfileExportService {
  async export_profile(
    profile: Profile,
    format: string,
    template_id?: string,
    options?: Record<string, any>
  ): Promise<[string, Blob]> {
    const response = await fetch('/api/profiler/export', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        profile_id: profile.id,
        format,
        template_id,
        options,
      }),
    });

    if (!response.ok) {
      throw new Error('Failed to export profile');
    }

    const filename = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'profile';
    const blob = await response.blob();

    return [filename, blob];
  }

  async get_templates(): Promise<any[]> {
    const response = await fetch('/api/profiler/templates');
    if (!response.ok) {
      throw new Error('Failed to fetch templates');
    }
    return response.json();
  }

  async create_template(template: any): Promise<any> {
    const response = await fetch('/api/profiler/templates', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(template),
    });

    if (!response.ok) {
      throw new Error('Failed to create template');
    }

    return response.json();
  }

  async update_template(template_id: string, template: any): Promise<any> {
    const response = await fetch(`/api/profiler/templates/${template_id}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(template),
    });

    if (!response.ok) {
      throw new Error('Failed to update template');
    }

    return response.json();
  }

  async delete_template(template_id: string): Promise<void> {
    const response = await fetch(`/api/profiler/templates/${template_id}`, {
      method: 'DELETE',
    });

    if (!response.ok) {
      throw new Error('Failed to delete template');
    }
  }

  async get_export_history(): Promise<any[]> {
    const response = await fetch('/api/profiler/exports/history');
    if (!response.ok) {
      throw new Error('Failed to fetch export history');
    }
    return response.json();
  }
} 