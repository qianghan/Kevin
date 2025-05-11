/**
 * Logger Service
 * 
 * This file provides logging functionality for the application.
 * It implements different log levels and can be configured to output logs
 * to different destinations (console, file, etc.).
 */

/**
 * Log levels enum
 */
export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARN = 2,
  ERROR = 3
}

/**
 * Global log level configuration
 */
let currentLogLevel: LogLevel = LogLevel.INFO;

/**
 * Configure the global log level
 */
export function setLogLevel(level: LogLevel): void {
  currentLogLevel = level;
}

/**
 * Get the current log level
 */
export function getLogLevel(): LogLevel {
  return currentLogLevel;
}

/**
 * Format a log message with timestamp
 */
function formatLogMessage(level: string, message: string): string {
  const timestamp = new Date().toISOString();
  return `[${timestamp}] [${level}] ${message}`;
}

/**
 * Log a debug message
 */
export function logDebug(message: string, ...args: any[]): void {
  if (currentLogLevel <= LogLevel.DEBUG) {
    console.debug(formatLogMessage('DEBUG', message), ...args);
  }
}

/**
 * Log an info message
 */
export function logInfo(message: string, ...args: any[]): void {
  if (currentLogLevel <= LogLevel.INFO) {
    console.info(formatLogMessage('INFO', message), ...args);
  }
}

/**
 * Log a warning message
 */
export function logWarn(message: string, ...args: any[]): void {
  if (currentLogLevel <= LogLevel.WARN) {
    console.warn(formatLogMessage('WARN', message), ...args);
  }
}

/**
 * Log an error message
 */
export function logError(message: string, error?: any, ...args: any[]): void {
  if (currentLogLevel <= LogLevel.ERROR) {
    console.error(formatLogMessage('ERROR', message), error, ...args);
  }
}

/**
 * Create a logger instance for a specific component
 */
export function createLogger(component: string) {
  return {
    debug: (message: string, ...args: any[]) => logDebug(`[${component}] ${message}`, ...args),
    info: (message: string, ...args: any[]) => logInfo(`[${component}] ${message}`, ...args),
    warn: (message: string, ...args: any[]) => logWarn(`[${component}] ${message}`, ...args),
    error: (message: string, error?: any, ...args: any[]) => logError(`[${component}] ${message}`, error, ...args)
  };
} 