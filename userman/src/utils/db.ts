import mongoose from 'mongoose';

/**
 * Database connection options
 */
interface DBOptions {
  uri: string;
  options?: mongoose.ConnectOptions;
}

/**
 * Default connection options
 */
const DEFAULT_OPTIONS: mongoose.ConnectOptions = {
  autoIndex: true,
  serverSelectionTimeoutMS: 5000,
};

/**
 * Connect to MongoDB database
 * 
 * @param options Database connection options
 * @returns Promise resolving to the mongoose connection
 */
export async function connectToDatabase(options: DBOptions): Promise<mongoose.Connection> {
  try {
    // Merge default options with provided options
    const connectOptions: mongoose.ConnectOptions = {
      ...DEFAULT_OPTIONS,
      ...options.options,
    };
    
    // Connect to MongoDB
    await mongoose.connect(options.uri, connectOptions);
    
    // Get the default connection
    const db = mongoose.connection;
    
    // Set up connection event handlers
    db.on('error', (error) => {
      console.error('MongoDB connection error:', error);
    });
    
    db.on('disconnected', () => {
      console.warn('MongoDB disconnected');
    });
    
    db.on('reconnected', () => {
      console.info('MongoDB reconnected');
    });
    
    console.info('Connected to MongoDB');
    
    return db;
  } catch (error) {
    console.error('Error connecting to MongoDB:', error);
    throw error;
  }
}

/**
 * Close the database connection
 * 
 * @returns Promise resolving when the connection is closed
 */
export async function closeDatabaseConnection(): Promise<void> {
  if (mongoose.connection.readyState !== 0) {
    await mongoose.connection.close();
    console.info('MongoDB connection closed');
  }
} 