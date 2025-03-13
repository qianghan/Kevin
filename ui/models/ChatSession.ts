import mongoose, { Document, Schema, Model } from 'mongoose';

// Define message structure for chat messages
export interface ChatMessage {
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  thinkingSteps?: any[]; // Store thinking steps from Kevin API
  documents?: any[]; // Store related documents from Kevin API
}

// Define ChatSession document interface
export interface ChatSessionDocument extends Document {
  title: string;
  userId: mongoose.Types.ObjectId;
  conversationId?: string; // Kevin API conversation ID
  messages: ChatMessage[];
  isActive: boolean;
  createdAt: Date;
  updatedAt: Date;
}

// Schema for individual messages
const MessageSchema = new Schema<ChatMessage>({
  role: {
    type: String,
    enum: ['user', 'assistant', 'system'],
    required: true
  },
  content: {
    type: String,
    required: true
  },
  timestamp: {
    type: Date,
    default: Date.now
  },
  thinkingSteps: {
    type: Schema.Types.Mixed,
    default: []
  },
  documents: {
    type: Schema.Types.Mixed,
    default: []
  }
});

// Define the schema for chat sessions
const ChatSessionSchema = new Schema<ChatSessionDocument>(
  {
    title: {
      type: String,
      required: true
    },
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true
    },
    conversationId: {
      type: String,
      sparse: true // Allow null/undefined values
    },
    messages: {
      type: [MessageSchema],
      default: []
    },
    isActive: {
      type: Boolean,
      default: true
    }
  },
  {
    timestamps: true
  }
);

// Static methods
interface ChatSessionModel extends Model<ChatSessionDocument> {
  findOrCreateSession(userId: mongoose.Types.ObjectId, title: string): Promise<ChatSessionDocument>;
  getActiveSessions(userId: mongoose.Types.ObjectId): Promise<ChatSessionDocument[]>;
  getSession(sessionId: mongoose.Types.ObjectId, userId: mongoose.Types.ObjectId): Promise<ChatSessionDocument | null>;
}

// Create a new session or return an existing empty one
ChatSessionSchema.statics.findOrCreateSession = async function(
  userId: mongoose.Types.ObjectId,
  title: string = 'New Chat'
): Promise<ChatSessionDocument> {
  // Try to find an existing active session with no messages
  let session = await this.findOne({
    userId,
    isActive: true,
    'messages.0': { $exists: false } // No messages yet
  });
  
  if (!session) {
    // Create a new session
    session = await this.create({
      title,
      userId,
      isActive: true,
      messages: []
    });
  }
  
  return session;
};

// Get all active sessions for a user
ChatSessionSchema.statics.getActiveSessions = async function(
  userId: mongoose.Types.ObjectId
): Promise<ChatSessionDocument[]> {
  return this.find({
    userId,
    isActive: true
  }).sort({ updatedAt: -1 });
};

// Get a specific session if it belongs to the user
ChatSessionSchema.statics.getSession = async function(
  sessionId: mongoose.Types.ObjectId,
  userId: mongoose.Types.ObjectId
): Promise<ChatSessionDocument | null> {
  return this.findOne({
    _id: sessionId,
    userId
  });
};

// Add message to the session
ChatSessionSchema.methods.addMessage = async function(
  message: Omit<ChatMessage, 'timestamp'>
) {
  this.messages.push({
    ...message,
    timestamp: new Date()
  });
  
  // Update title if it's the first user message and title is generic
  if (message.role === 'user' && 
      this.messages.length === 1 && 
      this.title === 'New Chat') {
    // Use the first ~30 chars of the message as the title
    this.title = message.content.substring(0, 30) + (message.content.length > 30 ? '...' : '');
  }
  
  return this.save();
};

// Check if the model exists before creating it to avoid "OverwriteModelError"
const ChatSession = (mongoose.models.ChatSession as ChatSessionModel) || 
  mongoose.model<ChatSessionDocument, ChatSessionModel>('ChatSession', ChatSessionSchema);

export default ChatSession; 