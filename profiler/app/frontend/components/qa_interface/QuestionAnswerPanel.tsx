import React, { useState, useEffect } from 'react';
import { Question, Answer, QuestionCategory } from '../../types/qa';
import { Box, Typography, TextField, Button, Card, CardContent, 
         CircularProgress, Chip, Grid, Paper, Tabs, Tab } from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import FeedbackIcon from '@mui/icons-material/Feedback';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import NavigateBeforeIcon from '@mui/icons-material/NavigateBefore';
import AttachFileIcon from '@mui/icons-material/AttachFile';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import LinearProgress from '@mui/material/LinearProgress';
import { styled } from '@mui/material/styles';

// Define category colors
const categoryColors = {
  professional: '#4caf50',
  education: '#2196f3',
  skills: '#ff9800',
  projects: '#9c27b0',
  default: '#757575'
};

// Styled components
const QuestionCard = styled(Card)(({ theme }) => ({
  marginBottom: theme.spacing(3),
  boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
  borderRadius: theme.spacing(1),
  transition: 'transform 0.2s ease-in-out',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
  },
}));

const CategoryChip = styled(Chip)<{ category: string }>(({ theme, category }) => ({
  backgroundColor: categoryColors[category as keyof typeof categoryColors] || categoryColors.default,
  color: '#fff',
  fontWeight: 500,
  marginRight: theme.spacing(1),
}));

const AnswerField = styled(TextField)(({ theme }) => ({
  marginTop: theme.spacing(2),
  marginBottom: theme.spacing(2),
  '& .MuiOutlinedInput-root': {
    borderRadius: theme.spacing(1),
  },
}));

const ProgressIndicator = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  marginBottom: theme.spacing(2),
}));

const ProgressText = styled(Typography)(({ theme }) => ({
  marginLeft: theme.spacing(1),
  color: theme.palette.text.secondary,
}));

interface QuestionAnswerPanelProps {
  profileId: string;
  onAnswerSubmit: (questionId: string, answer: string | { text: string, mediaType: string, mediaUrl: string }) => Promise<void>;
  onFeedbackSubmit: (questionId: string, feedback: string, rating: number) => Promise<void>;
  onLoadQuestions: (profileId: string) => Promise<Question[]>;
  onNavigateNextCategory?: () => void;
  className?: string;
}

const QuestionAnswerPanel: React.FC<QuestionAnswerPanelProps> = ({
  profileId,
  onAnswerSubmit,
  onFeedbackSubmit,
  onLoadQuestions,
  onNavigateNextCategory,
  className,
}) => {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState<number>(0);
  const [answerText, setAnswerText] = useState<string>('');
  const [feedbackText, setFeedbackText] = useState<string>('');
  const [feedbackRating, setFeedbackRating] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [submitting, setSubmitting] = useState<boolean>(false);
  const [showFeedback, setShowFeedback] = useState<boolean>(false);
  const [mediaFile, setMediaFile] = useState<File | null>(null);
  const [progress, setProgress] = useState<number>(0);
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);

  useEffect(() => {
    loadQuestions();
  }, [profileId]);

  useEffect(() => {
    if (questions.length > 0) {
      // Calculate progress
      const answered = questions.filter(q => q.answer).length;
      setProgress(Math.round((answered / questions.length) * 100));
    }
  }, [questions]);

  const loadQuestions = async () => {
    setLoading(true);
    try {
      const loadedQuestions = await onLoadQuestions(profileId);
      setQuestions(loadedQuestions);
      
      // Set current question to the first unanswered one
      const firstUnansweredIndex = loadedQuestions.findIndex(q => !q.answer);
      setCurrentQuestionIndex(firstUnansweredIndex >= 0 ? firstUnansweredIndex : 0);
      
      // Initialize category filter if questions exist
      if (loadedQuestions.length > 0) {
        const categories = [...new Set(loadedQuestions.map(q => q.category))];
        setSelectedCategory(categories[0]);
      }
    } catch (error) {
      console.error('Error loading questions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAnswerSubmit = async () => {
    if (!answerText.trim() && !mediaFile) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    setSubmitting(true);
    
    try {
      if (mediaFile) {
        // For multimedia answers
        const formData = new FormData();
        formData.append('file', mediaFile);
        formData.append('text', answerText);
        
        // In a real app, you'd upload the file and get a URL back
        const mockMediaUrl = URL.createObjectURL(mediaFile);
        
        await onAnswerSubmit(currentQuestion.id, {
          text: answerText,
          mediaType: mediaFile.type.split('/')[0], // 'image', 'audio', or 'video'
          mediaUrl: mockMediaUrl
        });
      } else {
        // For text-only answers
        await onAnswerSubmit(currentQuestion.id, answerText);
      }
      
      // Update the questions list with the new answer
      const updatedQuestions = [...questions];
      updatedQuestions[currentQuestionIndex] = {
        ...currentQuestion,
        answer: { text: answerText, submittedAt: new Date().toISOString() }
      };
      setQuestions(updatedQuestions);
      
      // Clear the form
      setAnswerText('');
      setMediaFile(null);
      
      // Move to the next question if available
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        // If all questions answered, show a completion message or move to the next section
        onNavigateNextCategory?.();
      }
    } catch (error) {
      console.error('Error submitting answer:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleFeedbackSubmit = async () => {
    if (!feedbackText.trim()) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    setSubmitting(true);
    
    try {
      await onFeedbackSubmit(currentQuestion.id, feedbackText, feedbackRating);
      
      // Clear the feedback form and hide it
      setFeedbackText('');
      setFeedbackRating(0);
      setShowFeedback(false);
      
      // Optionally update the UI to show the feedback was submitted
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setSubmitting(false);
    }
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files.length > 0) {
      setMediaFile(event.target.files[0]);
    }
  };

  const handleCategorySelect = (category: string) => {
    setSelectedCategory(category);
    
    // Find the first question in this category
    const index = questions.findIndex(q => q.category === category);
    if (index >= 0) {
      setCurrentQuestionIndex(index);
    }
  };

  const getFilteredQuestions = () => {
    if (!selectedCategory) return questions;
    return questions.filter(q => q.category === selectedCategory);
  };

  const getCurrentCategoryQuestions = () => {
    return getFilteredQuestions();
  };

  const getCurrentQuestionInCategory = () => {
    const categoryQuestions = getCurrentCategoryQuestions();
    if (categoryQuestions.length === 0) return null;
    
    // Find the current index within this category
    const currentQuestion = questions[currentQuestionIndex];
    const categoryIndex = categoryQuestions.findIndex(q => q.id === currentQuestion.id);
    
    return categoryIndex >= 0 ? categoryQuestions[categoryIndex] : categoryQuestions[0];
  };

  const navigateToPreviousQuestion = () => {
    if (currentQuestionIndex > 0) {
      setCurrentQuestionIndex(currentQuestionIndex - 1);
      setShowFeedback(false);
    }
  };

  const navigateToNextQuestion = () => {
    if (currentQuestionIndex < questions.length - 1) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
      setShowFeedback(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="300px">
        <CircularProgress />
      </Box>
    );
  }

  if (questions.length === 0) {
    return (
      <Box p={3} textAlign="center">
        <Typography variant="h6">No questions available for this profile.</Typography>
        <Button 
          variant="contained" 
          color="primary" 
          onClick={loadQuestions}
          sx={{ mt: 2 }}
        >
          Retry Loading Questions
        </Button>
      </Box>
    );
  }

  const currentQuestion = questions[currentQuestionIndex];
  const allCategories = [...new Set(questions.map(q => q.category))];

  return (
    <Box className={className}>
      {/* Progress indicator */}
      <ProgressIndicator>
        <LinearProgress variant="determinate" value={progress} sx={{ flexGrow: 1 }} />
        <ProgressText variant="body2">{progress}% Complete</ProgressText>
      </ProgressIndicator>
      
      {/* Category tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={selectedCategory}
          onChange={(_, value) => handleCategorySelect(value)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {allCategories.map(category => (
            <Tab 
              key={category} 
              label={category} 
              value={category}
              icon={
                questions.filter(q => q.category === category && q.answer).length === 
                questions.filter(q => q.category === category).length ? 
                <CheckCircleIcon fontSize="small" /> : undefined
              }
              iconPosition="end"
            />
          ))}
        </Tabs>
      </Paper>
      
      {/* Current question */}
      <QuestionCard>
        <CardContent>
          <Box display="flex" alignItems="center" mb={1}>
            <CategoryChip 
              label={currentQuestion.category} 
              category={currentQuestion.category}
              size="small"
            />
            <Typography variant="caption" color="text.secondary">
              Question {currentQuestionIndex + 1} of {questions.length}
            </Typography>
          </Box>
          
          <Typography variant="h6" gutterBottom>
            {currentQuestion.text}
          </Typography>
          
          {currentQuestion.answer ? (
            <Box mt={2} p={2} bgcolor="background.paper" borderRadius={1}>
              <Typography variant="subtitle1" fontWeight="bold">Your Answer:</Typography>
              <Typography variant="body1">{currentQuestion.answer.text}</Typography>
              
              {/* If there was a media attachment */}
              {currentQuestion.answer.mediaUrl && (
                <Box mt={2}>
                  {currentQuestion.answer.mediaType === 'image' ? (
                    <img 
                      src={currentQuestion.answer.mediaUrl} 
                      alt="Answer attachment" 
                      style={{ maxWidth: '100%', maxHeight: '200px', borderRadius: '4px' }}
                    />
                  ) : currentQuestion.answer.mediaType === 'audio' ? (
                    <audio controls src={currentQuestion.answer.mediaUrl} style={{ width: '100%' }} />
                  ) : currentQuestion.answer.mediaType === 'video' ? (
                    <video controls src={currentQuestion.answer.mediaUrl} style={{ maxWidth: '100%', borderRadius: '4px' }} />
                  ) : (
                    <Button variant="outlined" href={currentQuestion.answer.mediaUrl} target="_blank">
                      View Attachment
                    </Button>
                  )}
                </Box>
              )}
            </Box>
          ) : (
            <Box>
              <AnswerField
                fullWidth
                multiline
                rows={4}
                placeholder="Type your answer here..."
                value={answerText}
                onChange={(e) => setAnswerText(e.target.value)}
                disabled={submitting}
              />
              
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Button
                  component="label"
                  variant="outlined"
                  startIcon={<AttachFileIcon />}
                  disabled={submitting}
                >
                  Attach File
                  <input
                    type="file"
                    hidden
                    onChange={handleFileChange}
                    accept="image/*,audio/*,video/*"
                  />
                </Button>
                
                {mediaFile && (
                  <Typography variant="body2" color="text.secondary">
                    {mediaFile.name} ({(mediaFile.size / 1024).toFixed(1)} KB)
                  </Typography>
                )}
                
                <Button
                  variant="contained"
                  color="primary"
                  endIcon={<SendIcon />}
                  onClick={handleAnswerSubmit}
                  disabled={submitting || (!answerText.trim() && !mediaFile)}
                >
                  {submitting ? 'Submitting...' : 'Submit Answer'}
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </QuestionCard>
      
      {/* Feedback section (shown only for answered questions) */}
      {currentQuestion.answer && (
        <Box mt={2}>
          {showFeedback ? (
            <Card>
              <CardContent>
                <Typography variant="h6">Provide Feedback</Typography>
                <TextField
                  fullWidth
                  multiline
                  rows={2}
                  placeholder="Was this question helpful? Any suggestions for improvement?"
                  value={feedbackText}
                  onChange={(e) => setFeedbackText(e.target.value)}
                  margin="normal"
                />
                
                <Box display="flex" justifyContent="flex-end" mt={1}>
                  <Button 
                    onClick={() => setShowFeedback(false)}
                    sx={{ mr: 1 }}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    onClick={handleFeedbackSubmit}
                    disabled={submitting || !feedbackText.trim()}
                  >
                    Submit Feedback
                  </Button>
                </Box>
              </CardContent>
            </Card>
          ) : (
            <Button
              startIcon={<FeedbackIcon />}
              onClick={() => setShowFeedback(true)}
              variant="text"
              color="primary"
            >
              Provide Feedback
            </Button>
          )}
        </Box>
      )}
      
      {/* Navigation buttons */}
      <Box display="flex" justifyContent="space-between" mt={3}>
        <Button
          variant="outlined"
          startIcon={<NavigateBeforeIcon />}
          onClick={navigateToPreviousQuestion}
          disabled={currentQuestionIndex === 0}
        >
          Previous
        </Button>
        
        <Button
          variant="outlined"
          endIcon={<NavigateNextIcon />}
          onClick={navigateToNextQuestion}
          disabled={currentQuestionIndex === questions.length - 1}
        >
          Next
        </Button>
      </Box>
    </Box>
  );
};

export default QuestionAnswerPanel; 