/**
 * Logging Service Implementation
 * 
 * This is a concrete implementation of the ILoggingService interface.
 * It provides centralized logging functionality for the application.
 */

import { v4 as uuidv4 } from 'uuid';
import {
  ILoggingService,
  LogLevel,
  LogContext,
  LogEntry,
  LogOptions,
  PerformanceTimingOptions,
  LogTransportConfig
} from '../../interfaces/services/logging.service';

/**
 * Maximum number of logs to keep in memory
 */
const MAX_LOG_HISTORY = 1000;

/**
 * Default minimum log level
 */
const DEFAULT_MIN_LEVEL: LogLevel = process.env.NODE_ENV === 'production' ? 'info' : 'debug';

/**
 * Log level severity mapping (higher is more severe)
 */
const LOG_LEVEL_SEVERITY: Record<LogLevel, number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  fatal: 4
};

/**
 * Transport implementation for console logging
 */
class ConsoleTransport {
  private minLevel: LogLevel;
  
  constructor(minLevel: LogLevel = DEFAULT_MIN_LEVEL) {
    this.minLevel = minLevel;
  }
  
  public log(entry: LogEntry): void {
    if (LOG_LEVEL_SEVERITY[entry.level] < LOG_LEVEL_SEVERITY[this.minLevel]) {
      return;
    }
    
    const timestamp = new Date(entry.timestamp).toISOString();
    const prefix = `[${timestamp}] [${entry.level.toUpperCase()}]`;
    
    switch (entry.level) {
      case 'debug':
        console.debug(prefix, entry.message, entry.data || '');
        break;
      case 'info':
        console.info(prefix, entry.message, entry.data || '');
        break;
      case 'warn':
        console.warn(prefix, entry.message, entry.data || '');
        break;
      case 'error':
      case 'fatal':
        console.error(prefix, entry.message, entry.data || '', entry.context || '');
        break;
    }
  }
}

/**
 * Transport implementation for localStorage logging
 */
class LocalStorageTransport {
  private minLevel: LogLevel;
  private storageKey: string;
  private maxEntries: number;
  private buffer: LogEntry[] = [];
  private batchSize: number;
  private batchInterval: number;
  private batchTimer: NodeJS.Timeout | null = null;
  
  constructor(config: {
    minLevel?: LogLevel;
    storageKey?: string;
    maxEntries?: number;
    batchSize?: number;
    batchInterval?: number;
  } = {}) {
    this.minLevel = config.minLevel || DEFAULT_MIN_LEVEL;
    this.storageKey = config.storageKey || 'app_logs';
    this.maxEntries = config.maxEntries || 100;
    this.batchSize = config.batchSize || 10;
    this.batchInterval = config.batchInterval || 5000;
  }
  
  public log(entry: LogEntry): void {
    if (LOG_LEVEL_SEVERITY[entry.level] < LOG_LEVEL_SEVERITY[this.minLevel]) {
      return;
    }
    
    this.buffer.push(entry);
    
    if (this.buffer.length >= this.batchSize) {
      this.flush();
    } else if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => this.flush(), this.batchInterval);
    }
  }
  
  public flush(): void {
    if (this.buffer.length === 0) {
      return;
    }
    
    try {
      // Clear timeout if it exists
      if (this.batchTimer) {
        clearTimeout(this.batchTimer);
        this.batchTimer = null;
      }
      
      // Get existing logs
      let logs: LogEntry[] = [];
      const storedLogs = localStorage.getItem(this.storageKey);
      
      if (storedLogs) {
        logs = JSON.parse(storedLogs);
      }
      
      // Add new logs and limit to maxEntries
      logs = [...this.buffer, ...logs].slice(0, this.maxEntries);
      
      // Store updated logs
      localStorage.setItem(this.storageKey, JSON.stringify(logs));
      
      // Clear buffer
      this.buffer = [];
    } catch (error) {
      console.error('Error writing logs to localStorage:', error);
    }
  }
}

/**
 * Transport implementation for remote logging
 */
class RemoteTransport {
  private minLevel: LogLevel;
  private endpoint: string;
  private buffer: LogEntry[] = [];
  private batchSize: number;
  private batchInterval: number;
  private batchTimer: NodeJS.Timeout | null = null;
  
  constructor(config: {
    minLevel?: LogLevel;
    endpoint: string;
    batchSize?: number;
    batchInterval?: number;
  }) {
    this.minLevel = config.minLevel || DEFAULT_MIN_LEVEL;
    this.endpoint = config.endpoint;
    this.batchSize = config.batchSize || 10;
    this.batchInterval = config.batchInterval || 10000;
  }
  
  public log(entry: LogEntry): void {
    if (LOG_LEVEL_SEVERITY[entry.level] < LOG_LEVEL_SEVERITY[this.minLevel]) {
      return;
    }
    
    this.buffer.push(entry);
    
    if (this.buffer.length >= this.batchSize) {
      this.flush();
    } else if (!this.batchTimer) {
      this.batchTimer = setTimeout(() => this.flush(), this.batchInterval);
    }
  }
  
  public async flush(): Promise<void> {
    if (this.buffer.length === 0) {
      return;
    }
    
    // Clear timeout if it exists
    if (this.batchTimer) {
      clearTimeout(this.batchTimer);
      this.batchTimer = null;
    }
    
    const logsToSend = [...this.buffer];
    this.buffer = [];
    
    try {
      // Send logs to remote endpoint
      await fetch(this.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ logs: logsToSend }),
      });
    } catch (error) {
      console.error('Error sending logs to remote endpoint:', error);
      // Add logs back to buffer for retry
      this.buffer = [...logsToSend, ...this.buffer];
    }
  }
}

/**
 * Logging Service implementation
 */
export class LoggingService implements ILoggingService {
  private logHistory: LogEntry[] = [];
  private globalContext: Partial<LogContext> = {};
  private transports: Array<ConsoleTransport | LocalStorageTransport | RemoteTransport> = [];
  
  constructor() {
    // Add console transport by default
    this.transports.push(new ConsoleTransport());
  }
  
  /**
   * Log a message at a specific level
   */
  public log(level: LogLevel, message: string, options: LogOptions = {}): LogEntry {
    // Prepare context by combining global and local context
    const context: LogContext = {
      ...this.globalContext,
      ...options.context || {},
    };
    
    // Create log entry
    const logEntry: LogEntry = {
      id: uuidv4(),
      timestamp: new Date().toISOString(),
      level,
      message,
      context,
      tags: options.tags || [],
      data: options.data,
    };
    
    // Add to log history, keeping only the most recent logs
    this.logHistory = [logEntry, ...this.logHistory.slice(0, MAX_LOG_HISTORY - 1)];
    
    // Send to all transports
    this.transports.forEach(transport => {
      transport.log(logEntry);
    });
    
    return logEntry;
  }
  
  /**
   * Log a debug message
   */
  public debug(message: string, options?: LogOptions): LogEntry {
    return this.log('debug', message, options);
  }
  
  /**
   * Log an info message
   */
  public info(message: string, options?: LogOptions): LogEntry {
    return this.log('info', message, options);
  }
  
  /**
   * Log a warning message
   */
  public warn(message: string, options?: LogOptions): LogEntry {
    return this.log('warn', message, options);
  }
  
  /**
   * Log an error message
   */
  public error(message: string, error?: Error, options: LogOptions = {}): LogEntry {
    const errorData = error ? {
      ...(options.data || {}),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name,
      }
    } : options.data;
    
    return this.log('error', message, {
      ...options,
      data: errorData,
    });
  }
  
  /**
   * Log a fatal message
   */
  public fatal(message: string, error?: Error, options: LogOptions = {}): LogEntry {
    const errorData = error ? {
      ...(options.data || {}),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name,
      }
    } : options.data;
    
    return this.log('fatal', message, {
      ...options,
      data: errorData,
    });
  }
  
  /**
   * Time an operation and log its duration
   */
  public time<T>(operation: string, fn: () => T, options: PerformanceTimingOptions = {}): T {
    const start = performance.now();
    
    try {
      // Execute the function
      const result = fn();
      
      // Calculate duration
      const duration = performance.now() - start;
      
      // Log only if duration exceeds threshold (if provided)
      if (!options.threshold || duration >= options.threshold) {
        this.info(`Operation "${operation}" completed in ${duration.toFixed(2)}ms`, {
          tags: [...(options.tags || []), 'performance'],
          data: { operation, duration },
        });
      }
      
      return result;
    } catch (error) {
      // Calculate duration even if operation failed
      const duration = performance.now() - start;
      
      this.error(`Operation "${operation}" failed after ${duration.toFixed(2)}ms`, error as Error, {
        tags: [...(options.tags || []), 'performance', 'error'],
        data: { operation, duration },
      });
      
      throw error;
    }
  }
  
  /**
   * Time an async operation and log its duration
   */
  public async timeAsync<T>(operation: string, fn: () => Promise<T>, options: PerformanceTimingOptions = {}): Promise<T> {
    const start = performance.now();
    
    try {
      // Execute the async function
      const result = await fn();
      
      // Calculate duration
      const duration = performance.now() - start;
      
      // Log only if duration exceeds threshold (if provided)
      if (!options.threshold || duration >= options.threshold) {
        this.info(`Async operation "${operation}" completed in ${duration.toFixed(2)}ms`, {
          tags: [...(options.tags || []), 'performance', 'async'],
          data: { operation, duration },
        });
      }
      
      return result;
    } catch (error) {
      // Calculate duration even if operation failed
      const duration = performance.now() - start;
      
      this.error(`Async operation "${operation}" failed after ${duration.toFixed(2)}ms`, error as Error, {
        tags: [...(options.tags || []), 'performance', 'async', 'error'],
        data: { operation, duration },
      });
      
      throw error;
    }
  }
  
  /**
   * Start timing an operation
   */
  public startTimer(operation: string, options: PerformanceTimingOptions = {}): () => number {
    const start = performance.now();
    
    return () => {
      const duration = performance.now() - start;
      
      // Log only if duration exceeds threshold (if provided)
      if (!options.threshold || duration >= options.threshold) {
        this.info(`Operation "${operation}" completed in ${duration.toFixed(2)}ms`, {
          tags: [...(options.tags || []), 'performance'],
          data: { operation, duration },
        });
      }
      
      return duration;
    };
  }
  
  /**
   * Set global context for all log entries
   */
  public setGlobalContext(context: Partial<LogContext>): void {
    this.globalContext = {
      ...this.globalContext,
      ...context,
    };
  }
  
  /**
   * Add a transport for log entries
   */
  public addTransport(config: LogTransportConfig): boolean {
    try {
      switch (config.type) {
        case 'console':
          this.transports.push(new ConsoleTransport(config.minLevel));
          break;
        case 'localStorage':
          this.transports.push(new LocalStorageTransport({
            minLevel: config.minLevel,
            batchSize: config.batchSize,
            batchInterval: config.batchInterval,
          }));
          break;
        case 'remote':
          if (!config.endpoint) {
            throw new Error('Remote transport requires an endpoint');
          }
          this.transports.push(new RemoteTransport({
            minLevel: config.minLevel,
            endpoint: config.endpoint,
            batchSize: config.batchSize,
            batchInterval: config.batchInterval,
          }));
          break;
        default:
          throw new Error(`Unknown transport type: ${config.type}`);
      }
      
      return true;
    } catch (error) {
      console.error('Error adding transport:', error);
      return false;
    }
  }
  
  /**
   * Get all log entries matching filter criteria
   */
  public getEntries(filter?: {
    level?: LogLevel | LogLevel[];
    tags?: string[];
    from?: string;
    to?: string;
  }): LogEntry[] {
    if (!filter) {
      return [...this.logHistory];
    }
    
    return this.logHistory.filter(entry => {
      // Filter by level
      if (filter.level) {
        const levels = Array.isArray(filter.level) ? filter.level : [filter.level];
        if (!levels.includes(entry.level)) {
          return false;
        }
      }
      
      // Filter by tags
      if (filter.tags && filter.tags.length > 0) {
        if (!entry.tags || !filter.tags.some(tag => entry.tags?.includes(tag))) {
          return false;
        }
      }
      
      // Filter by date range
      if (filter.from) {
        const fromDate = new Date(filter.from).getTime();
        const entryDate = new Date(entry.timestamp).getTime();
        if (entryDate < fromDate) {
          return false;
        }
      }
      
      if (filter.to) {
        const toDate = new Date(filter.to).getTime();
        const entryDate = new Date(entry.timestamp).getTime();
        if (entryDate > toDate) {
          return false;
        }
      }
      
      return true;
    });
  }
  
  /**
   * Flush any buffered log entries to their destinations
   */
  public async flush(): Promise<void> {
    const flushPromises = this.transports.map(async transport => {
      if ('flush' in transport && typeof transport.flush === 'function') {
        await transport.flush();
      }
    });
    
    await Promise.all(flushPromises);
  }
} 