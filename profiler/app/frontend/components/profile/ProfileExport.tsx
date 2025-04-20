import React, { useState } from 'react';
import {
  Box,
  Button,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  CircularProgress,
  Typography,
  Snackbar,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  CardActions,
} from '@mui/material';
import { useProfile } from '../../hooks/useProfile';
import { useAuth } from '../../hooks/useAuth';
import { ProfileExportService } from '../../services/profile/export';

interface ExportFormat {
  id: string;
  label: string;
  description: string;
}

interface ExportTemplate {
  id: string;
  name: string;
  description: string;
  format: string;
}

const exportFormats: ExportFormat[] = [
  { id: 'pdf', label: 'PDF', description: 'Professional document format' },
  { id: 'docx', label: 'Word', description: 'Editable document format' },
  { id: 'html', label: 'HTML', description: 'Web page format' },
  { id: 'markdown', label: 'Markdown', description: 'Plain text with formatting' },
  { id: 'json', label: 'JSON', description: 'Structured data format' },
  { id: 'yaml', label: 'YAML', description: 'Human-readable data format' },
  { id: 'csv', label: 'CSV', description: 'Spreadsheet format' },
];

const ProfileExport: React.FC = () => {
  const { profile } = useProfile();
  const { user } = useAuth();
  const [selectedFormat, setSelectedFormat] = useState<string>('');
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [templates, setTemplates] = useState<ExportTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState<string>('');

  const handleFormatChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedFormat(event.target.value as string);
  };

  const handleTemplateChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setSelectedTemplate(event.target.value as string);
  };

  const handleExport = async () => {
    if (!profile || !user) return;

    try {
      setLoading(true);
      setError(null);

      const exportService = new ProfileExportService();
      const [filename, content] = await exportService.export_profile(
        profile,
        selectedFormat,
        selectedTemplate || undefined
      );

      // Create download link
      const blob = new Blob([await content.arrayBuffer()], {
        type: `application/${selectedFormat}`,
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setSuccess('Profile exported successfully!');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to export profile');
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    if (!profile || !user) return;

    try {
      setLoading(true);
      setError(null);

      const exportService = new ProfileExportService();
      const [_, content] = await exportService.export_profile(
        profile,
        'html',
        selectedTemplate || undefined
      );

      const text = await content.text();
      setPreviewContent(text);
      setPreviewOpen(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate preview');
    } finally {
      setLoading(false);
    }
  };

  const handleClosePreview = () => {
    setPreviewOpen(false);
    setPreviewContent('');
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h5" gutterBottom>
        Export Profile
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export Options
              </Typography>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Format</InputLabel>
                <Select
                  value={selectedFormat}
                  onChange={handleFormatChange}
                  label="Format"
                >
                  {exportFormats.map((format) => (
                    <MenuItem key={format.id} value={format.id}>
                      {format.label}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Template</InputLabel>
                <Select
                  value={selectedTemplate}
                  onChange={handleTemplateChange}
                  label="Template"
                >
                  <MenuItem value="">Default Template</MenuItem>
                  {templates.map((template) => (
                    <MenuItem key={template.id} value={template.id}>
                      {template.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </CardContent>

            <CardActions>
              <Button
                variant="contained"
                onClick={handleExport}
                disabled={!selectedFormat || loading}
              >
                {loading ? <CircularProgress size={24} /> : 'Export'}
              </Button>
              <Button
                variant="outlined"
                onClick={handlePreview}
                disabled={loading}
              >
                Preview
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Export History
              </Typography>
              {/* Export history will be implemented later */}
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Dialog
        open={previewOpen}
        onClose={handleClosePreview}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>Profile Preview</DialogTitle>
        <DialogContent>
          <div dangerouslySetInnerHTML={{ __html: previewContent }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClosePreview}>Close</Button>
        </DialogActions>
      </Dialog>

      <Snackbar
        open={!!error}
        autoHideDuration={6000}
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>

      <Snackbar
        open={!!success}
        autoHideDuration={6000}
        onClose={() => setSuccess(null)}
      >
        <Alert severity="success" onClose={() => setSuccess(null)}>
          {success}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default ProfileExport; 