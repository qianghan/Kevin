import React, { useState, useRef } from 'react';
import {
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControl,
  FormControlLabel,
  FormGroup,
  FormHelperText,
  IconButton,
  InputLabel,
  MenuItem,
  Select,
  Switch,
  TextField,
  Tooltip,
  Typography,
  Snackbar,
  Alert,
  Tabs,
  Tab,
  Paper,
  Chip
} from '@mui/material';
import {
  DownloadOutlined,
  ShareOutlined,
  ContentCopyOutlined,
  EmailOutlined,
  LinkOutlined,
  CodeOutlined,
  CheckCircleOutline,
  FileCopyOutlined
} from '@mui/icons-material';
import { useDocumentContext } from '../../context/DocumentContext';
import { useAuthContext } from '../../context/AuthContext';

interface ExportOption {
  value: string;
  label: string;
  icon?: React.ReactNode;
}

interface ShareRecipient {
  email: string;
  error?: string;
}

interface DocumentExportProps {
  documentId: string;
  documentTitle: string;
  onClose?: () => void;
  disableEmbedding?: boolean;
}

/**
 * DocumentExport component for exporting, sharing and embedding documents.
 * Provides options to:
 * - Export documents in various formats (PDF, DOCX, HTML, TXT, JSON)
 * - Share documents via email with customized messages
 * - Generate and copy shareable links
 * - Create embed code for external websites
 */
const DocumentExport: React.FC<DocumentExportProps> = ({
  documentId,
  documentTitle,
  onClose,
  disableEmbedding = false
}) => {
  // Tab state
  const [activeTab, setActiveTab] = useState<number>(0);
  
  // Export state
  const [exportFormat, setExportFormat] = useState<string>('pdf');
  const [isExporting, setIsExporting] = useState<boolean>(false);
  
  // Share state
  const [shareMethod, setShareMethod] = useState<'email' | 'link'>('email');
  const [recipients, setRecipients] = useState<ShareRecipient[]>([{ email: '' }]);
  const [shareMessage, setShareMessage] = useState<string>('');
  const [attachDocument, setAttachDocument] = useState<boolean>(true);
  const [attachFormat, setAttachFormat] = useState<string>('pdf');
  const [expiryDays, setExpiryDays] = useState<number>(7);
  const [shareUrl, setShareUrl] = useState<string>('');
  const [isSharing, setIsSharing] = useState<boolean>(false);
  
  // Embed state
  const [embedWidth, setEmbedWidth] = useState<string>('100%');
  const [embedHeight, setEmbedHeight] = useState<string>('500px');
  const [showToolbar, setShowToolbar] = useState<boolean>(true);
  const [embedCode, setEmbedCode] = useState<string>('');
  
  // Notification state
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info'
  });
  
  // Refs
  const linkRef = useRef<HTMLInputElement>(null);
  const embedRef = useRef<HTMLTextAreaElement>(null);
  
  // Context
  const { exportDocument, shareDocument, generateEmbedCode } = useDocumentContext();
  const { user } = useAuthContext();
  
  // Export options
  const exportOptions: ExportOption[] = [
    { value: 'pdf', label: 'PDF Document' },
    { value: 'docx', label: 'Word Document (DOCX)' },
    { value: 'html', label: 'HTML Page' },
    { value: 'txt', label: 'Plain Text' },
    { value: 'json', label: 'JSON Data' }
  ];
  
  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };
  
  // Export handlers
  const handleExportFormatChange = (event: React.ChangeEvent<{ value: unknown }>) => {
    setExportFormat(event.target.value as string);
  };
  
  const handleExport = async () => {
    if (!documentId) return;
    
    setIsExporting(true);
    try {
      await exportDocument(documentId, exportFormat);
      showNotification('Document exported successfully', 'success');
    } catch (error) {
      console.error('Export error:', error);
      showNotification('Failed to export document', 'error');
    } finally {
      setIsExporting(false);
    }
  };
  
  // Share handlers
  const handleAddRecipient = () => {
    setRecipients([...recipients, { email: '' }]);
  };
  
  const handleRemoveRecipient = (index: number) => {
    const newRecipients = [...recipients];
    newRecipients.splice(index, 1);
    setRecipients(newRecipients);
  };
  
  const handleRecipientChange = (index: number, value: string) => {
    const newRecipients = [...recipients];
    newRecipients[index] = { 
      email: value,
      error: validateEmail(value) ? undefined : 'Invalid email'
    };
    setRecipients(newRecipients);
  };
  
  const validateEmail = (email: string): boolean => {
    if (!email) return false;
    const re = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return re.test(email);
  };
  
  const validateRecipients = (): boolean => {
    if (shareMethod === 'link') return true;
    
    // Check if at least one valid email is provided
    const validRecipients = recipients.filter(
      r => r.email && validateEmail(r.email)
    );
    return validRecipients.length > 0;
  };
  
  const handleShare = async () => {
    if (!documentId || !validateRecipients()) return;
    
    setIsSharing(true);
    try {
      const validEmails = recipients
        .filter(r => r.email && validateEmail(r.email))
        .map(r => r.email);
      
      const result = await shareDocument({
        documentId,
        recipients: validEmails,
        message: shareMessage,
        method: shareMethod,
        format: attachDocument ? attachFormat : undefined,
        expiryDays
      });
      
      if (result && result.share_url) {
        setShareUrl(result.share_url);
        if (shareMethod === 'link') {
          setTimeout(() => {
            if (linkRef.current) {
              linkRef.current.select();
            }
          }, 100);
        }
        showNotification(
          shareMethod === 'email' 
            ? 'Document shared successfully via email' 
            : 'Share link generated successfully',
          'success'
        );
      }
    } catch (error) {
      console.error('Share error:', error);
      showNotification('Failed to share document', 'error');
    } finally {
      setIsSharing(false);
    }
  };
  
  const handleCopyLink = () => {
    if (linkRef.current) {
      linkRef.current.select();
      document.execCommand('copy');
      showNotification('Link copied to clipboard', 'success');
    }
  };
  
  // Embed handlers
  const handleGenerateEmbedCode = () => {
    if (!documentId) return;
    
    try {
      const code = generateEmbedCode(documentId, {
        width: embedWidth,
        height: embedHeight,
        toolbar: showToolbar
      });
      setEmbedCode(code);
      
      setTimeout(() => {
        if (embedRef.current) {
          embedRef.current.select();
        }
      }, 100);
    } catch (error) {
      console.error('Embed code generation error:', error);
      showNotification('Failed to generate embed code', 'error');
    }
  };
  
  const handleCopyEmbedCode = () => {
    if (embedRef.current) {
      embedRef.current.select();
      document.execCommand('copy');
      showNotification('Embed code copied to clipboard', 'success');
    }
  };
  
  // Utility functions
  const showNotification = (message: string, severity: 'success' | 'error' | 'info') => {
    setNotification({
      open: true,
      message,
      severity
    });
  };
  
  const handleCloseNotification = () => {
    setNotification({
      ...notification,
      open: false
    });
  };
  
  return (
    <Card elevation={3}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="h2">
            {documentTitle || 'Document'}
          </Typography>
          {onClose && (
            <Button size="small" onClick={onClose}>Close</Button>
          )}
        </Box>
        
        <Paper elevation={0} sx={{ mb: 2 }}>
          <Tabs 
            value={activeTab} 
            onChange={handleTabChange}
            indicatorColor="primary"
            textColor="primary"
            variant="fullWidth"
          >
            <Tab icon={<DownloadOutlined />} label="Export" />
            <Tab icon={<ShareOutlined />} label="Share" />
            {!disableEmbedding && <Tab icon={<CodeOutlined />} label="Embed" />}
          </Tabs>
        </Paper>
        
        {/* Export Tab */}
        {activeTab === 0 && (
          <Box>
            <Typography variant="body2" color="textSecondary" paragraph>
              Export this document in your preferred format
            </Typography>
            
            <FormControl fullWidth margin="normal">
              <InputLabel id="export-format-label">Export Format</InputLabel>
              <Select
                labelId="export-format-label"
                value={exportFormat}
                onChange={handleExportFormatChange}
                label="Export Format"
              >
                {exportOptions.map((option) => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            
            <Box sx={{ mt: 3, display: 'flex', justifyContent: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={isExporting ? <CircularProgress size={20} color="inherit" /> : <DownloadOutlined />}
                onClick={handleExport}
                disabled={isExporting}
                fullWidth
              >
                {isExporting ? 'Exporting...' : 'Export Document'}
              </Button>
            </Box>
          </Box>
        )}
        
        {/* Share Tab */}
        {activeTab === 1 && (
          <Box>
            <FormControl component="fieldset" sx={{ mb: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Share Method
              </Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <Button
                  variant={shareMethod === 'email' ? 'contained' : 'outlined'}
                  startIcon={<EmailOutlined />}
                  onClick={() => setShareMethod('email')}
                  color={shareMethod === 'email' ? 'primary' : 'inherit'}
                >
                  Email
                </Button>
                <Button
                  variant={shareMethod === 'link' ? 'contained' : 'outlined'}
                  startIcon={<LinkOutlined />}
                  onClick={() => setShareMethod('link')}
                  color={shareMethod === 'link' ? 'primary' : 'inherit'}
                >
                  Share Link
                </Button>
              </Box>
            </FormControl>
            
            <Divider sx={{ my: 2 }} />
            
            {shareMethod === 'email' && (
              <>
                <Typography variant="body2" color="textSecondary" gutterBottom>
                  Recipients
                </Typography>
                
                {recipients.map((recipient, index) => (
                  <Box key={index} sx={{ display: 'flex', alignItems: 'flex-start', mb: 1 }}>
                    <TextField
                      fullWidth
                      label={`Recipient ${index + 1}`}
                      value={recipient.email}
                      onChange={(e) => handleRecipientChange(index, e.target.value)}
                      error={Boolean(recipient.error)}
                      helperText={recipient.error}
                      margin="dense"
                      size="small"
                    />
                    <IconButton 
                      size="small" 
                      color="error" 
                      sx={{ mt: 1, ml: 1 }} 
                      onClick={() => handleRemoveRecipient(index)}
                      disabled={recipients.length === 1}
                    >
                      &times;
                    </IconButton>
                  </Box>
                ))}
                
                <Button 
                  size="small" 
                  color="primary" 
                  onClick={handleAddRecipient}
                  sx={{ mb: 2 }}
                >
                  + Add Recipient
                </Button>
                
                <TextField
                  fullWidth
                  label="Message (Optional)"
                  multiline
                  rows={3}
                  value={shareMessage}
                  onChange={(e) => setShareMessage(e.target.value)}
                  margin="normal"
                  variant="outlined"
                />
                
                <FormGroup sx={{ my: 2 }}>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={attachDocument}
                        onChange={(e) => setAttachDocument(e.target.checked)}
                        color="primary"
                      />
                    }
                    label="Attach document to email"
                  />
                  
                  {attachDocument && (
                    <FormControl sx={{ mt: 1, ml: 2 }} size="small">
                      <InputLabel id="attach-format-label">Format</InputLabel>
                      <Select
                        labelId="attach-format-label"
                        value={attachFormat}
                        onChange={(e) => setAttachFormat(e.target.value as string)}
                        label="Format"
                      >
                        {exportOptions.map((option) => (
                          <MenuItem key={option.value} value={option.value}>
                            {option.label}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  )}
                </FormGroup>
              </>
            )}
            
            {/* Link expiration settings (both methods) */}
            <Box sx={{ my: 2 }}>
              <Typography variant="body2" color="textSecondary" gutterBottom>
                Link Expiration
              </Typography>
              <FormControl size="small" fullWidth>
                <InputLabel id="expiry-label">Expires After</InputLabel>
                <Select
                  labelId="expiry-label"
                  value={expiryDays}
                  onChange={(e) => setExpiryDays(Number(e.target.value))}
                  label="Expires After"
                >
                  <MenuItem value={1}>1 day</MenuItem>
                  <MenuItem value={7}>7 days</MenuItem>
                  <MenuItem value={14}>14 days</MenuItem>
                  <MenuItem value={30}>30 days</MenuItem>
                </Select>
              </FormControl>
            </Box>
            
            {/* Share link (shown after generating) */}
            {shareUrl && (
              <Box sx={{ mt: 2, mb: 3 }}>
                <Typography variant="body2" color="primary" gutterBottom>
                  Share Link
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <TextField
                    fullWidth
                    value={shareUrl}
                    inputRef={linkRef}
                    InputProps={{ readOnly: true }}
                    variant="outlined"
                    size="small"
                  />
                  <Tooltip title="Copy Link">
                    <IconButton color="primary" onClick={handleCopyLink} sx={{ ml: 1 }}>
                      <ContentCopyOutlined />
                    </IconButton>
                  </Tooltip>
                </Box>
                <FormHelperText>
                  This link will expire in {expiryDays} day{expiryDays !== 1 ? 's' : ''}
                </FormHelperText>
              </Box>
            )}
            
            <Box sx={{ mt: 3 }}>
              <Button
                variant="contained"
                color="primary"
                startIcon={isSharing ? <CircularProgress size={20} color="inherit" /> : <ShareOutlined />}
                onClick={handleShare}
                disabled={isSharing || (shareMethod === 'email' && !validateRecipients())}
                fullWidth
              >
                {isSharing ? 'Processing...' : shareMethod === 'email' ? 'Send Email' : 'Generate Link'}
              </Button>
            </Box>
          </Box>
        )}
        
        {/* Embed Tab */}
        {activeTab === 2 && !disableEmbedding && (
          <Box>
            <Typography variant="body2" color="textSecondary" paragraph>
              Create an embed code to display this document on your website
            </Typography>
            
            <Box sx={{ mt: 2 }}>
              <Typography variant="body2" gutterBottom>Embed Size</Typography>
              <Box sx={{ display: 'flex', gap: 2 }}>
                <TextField
                  label="Width"
                  value={embedWidth}
                  onChange={(e) => setEmbedWidth(e.target.value)}
                  variant="outlined"
                  size="small"
                  sx={{ flex: 1 }}
                  helperText="e.g., 100%, 600px"
                />
                <TextField
                  label="Height"
                  value={embedHeight}
                  onChange={(e) => setEmbedHeight(e.target.value)}
                  variant="outlined"
                  size="small"
                  sx={{ flex: 1 }}
                  helperText="e.g., 500px"
                />
              </Box>
            </Box>
            
            <FormGroup sx={{ my: 2 }}>
              <FormControlLabel
                control={
                  <Switch
                    checked={showToolbar}
                    onChange={(e) => setShowToolbar(e.target.checked)}
                    color="primary"
                  />
                }
                label="Show document toolbar"
              />
            </FormGroup>
            
            <Button
              variant="contained"
              color="primary"
              onClick={handleGenerateEmbedCode}
              startIcon={<CodeOutlined />}
              fullWidth
              sx={{ mt: 2, mb: 3 }}
            >
              Generate Embed Code
            </Button>
            
            {embedCode && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="body2" color="primary" gutterBottom>
                  Embed Code
                </Typography>
                <Box sx={{ position: 'relative' }}>
                  <TextField
                    fullWidth
                    multiline
                    rows={4}
                    value={embedCode}
                    inputRef={embedRef}
                    InputProps={{ readOnly: true }}
                    variant="outlined"
                    size="small"
                  />
                  <Box sx={{ position: 'absolute', top: 8, right: 8 }}>
                    <Tooltip title="Copy Code">
                      <IconButton color="primary" onClick={handleCopyEmbedCode} size="small">
                        <FileCopyOutlined fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </Box>
                </Box>
                
                <Typography variant="caption" color="textSecondary" sx={{ mt: 1, display: 'block' }}>
                  Paste this code into your website's HTML to embed the document
                </Typography>
                
                <Box sx={{ mt: 3 }}>
                  <Typography variant="body2" gutterBottom>Preview:</Typography>
                  <Box
                    sx={{
                      border: '1px dashed #ccc',
                      p: 2,
                      backgroundColor: '#f5f5f5',
                      height: '200px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center'
                    }}
                  >
                    <Typography variant="body2" color="textSecondary">
                      Document preview will appear here when embedded
                    </Typography>
                  </Box>
                </Box>
              </Box>
            )}
          </Box>
        )}
        
        <Snackbar
          open={notification.open}
          autoHideDuration={5000}
          onClose={handleCloseNotification}
          anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
        >
          <Alert 
            onClose={handleCloseNotification} 
            severity={notification.severity}
            variant="filled"
          >
            {notification.message}
          </Alert>
        </Snackbar>
      </CardContent>
    </Card>
  );
};

export default DocumentExport; 