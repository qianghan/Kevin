/**
 * Logging Service Interface
 * 
 * Defines the contract for logging operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to logging.
 */

export type LogLevel = 'debug' | 'info' | 'warn' | 'error' | 'fatal';

export type LogTransportType = 'console' | 'remote' | 'localStorage';

export interface LogContext {
  userId?: string;
  sessionId?: string;
  requestId?: string;
  feature?: string;
  component?: string;
  [key: string]: any;
}

export interface LogEntry {
  id: string;
  timestamp: string;
  level: LogLevel;
  message: string;
  context: LogContext;
  tags?: string[];
  data?: Record<string, any>;
}

export interface LogOptions {
  tags?: string[];
  context?: Partial<LogContext>;
  data?: Record<string, any>;
}

export interface PerformanceTimingOptions {
  tags?: string[];
  threshold?: number; // Log only if operation takes longer than threshold (ms)
}

export interface LogTransportConfig {
  type: LogTransportType;
  minLevel: LogLevel;
  batchSize?: number;
  batchInterval?: number; // In milliseconds
  endpoint?: string; // For remote transport
}

export interface ILoggingService {
  /**
   * Log a message at a specific level
   * @param level Log level
   * @param message Message to log
   * @param options Log options
   * @returns Generated log entry
   */
  log(level: LogLevel, message: string, options?: LogOptions): LogEntry;
  
  /**
   * Log a debug message
   * @param message Message to log
   * @param options Log options
   * @returns Generated log entry
   */
  debug(message: string, options?: LogOptions): LogEntry;
  
  /**
   * Log an info message
   * @param message Message to log
   * @param options Log options
   * @returns Generated log entry
   */
  info(message: string, options?: LogOptions): LogEntry;
  
  /**
   * Log a warning message
   * @param message Message to log
   * @param options Log options
   * @returns Generated log entry
   */
  warn(message: string, options?: LogOptions): LogEntry;
  
  /**
   * Log an error message
   * @param message Message to log
   * @param error Error object
   * @param options Log options
   * @returns Generated log entry
   */
  error(message: string, error?: Error, options?: LogOptions): LogEntry;
  
  /**
   * Log a fatal message
   * @param message Message to log
   * @param error Error object
   * @param options Log options
   * @returns Generated log entry
   */
  fatal(message: string, error?: Error, options?: LogOptions): LogEntry;
  
  /**
   * Time an operation and log its duration
   * @param operation Operation name
   * @param fn Function to time
   * @param options Performance timing options
   * @returns Result of the timed function
   */
  time<T>(operation: string, fn: () => T, options?: PerformanceTimingOptions): T;
  
  /**
   * Time an async operation and log its duration
   * @param operation Operation name
   * @param fn Async function to time
   * @param options Performance timing options
   * @returns Promise resolving to the result of the timed function
   */
  timeAsync<T>(operation: string, fn: () => Promise<T>, options?: PerformanceTimingOptions): Promise<T>;
  
  /**
   * Start timing an operation
   * @param operation Operation name
   * @returns Stop function that ends timing and logs duration
   */
  startTimer(operation: string, options?: PerformanceTimingOptions): () => number;
  
  /**
   * Set global context for all log entries
   * @param context Context to include with all logs
   */
  setGlobalContext(context: Partial<LogContext>): void;
  
  /**
   * Add a transport for log entries
   * @param config Transport configuration
   * @returns True if transport was added successfully
   */
  addTransport(config: LogTransportConfig): boolean;
  
  /**
   * Get all log entries matching filter criteria
   * @param filter Filter criteria
   * @returns Filtered log entries
   */
  getEntries(filter?: {
    level?: LogLevel | LogLevel[];
    tags?: string[];
    from?: string;
    to?: string;
  }): LogEntry[];
  
  /**
   * Flush any buffered log entries to their destinations
   * @returns Promise resolving when flush is complete
   */
  flush(): Promise<void>;
} 