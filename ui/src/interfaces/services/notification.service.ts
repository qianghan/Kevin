/**
 * Notification Service Interface
 * 
 * Defines the contract for notification-related operations.
 * This follows the Interface Segregation Principle by including
 * only methods related to user notifications.
 */

export type NotificationType = 'info' | 'success' | 'warning' | 'error';

export type NotificationPosition = 
  | 'top' 
  | 'top-right' 
  | 'top-left' 
  | 'bottom' 
  | 'bottom-right' 
  | 'bottom-left';

export interface Notification {
  id: string;
  title?: string;
  message: string;
  type: NotificationType;
  createdAt: string;
  read: boolean;
  actionUrl?: string;
  actionLabel?: string;
  metadata?: Record<string, any>;
}

export interface NotificationOptions {
  duration?: number;
  position?: NotificationPosition;
  isClosable?: boolean;
  onClose?: () => void;
  onAction?: () => void;
}

export interface INotificationService {
  /**
   * Show a toast notification
   * @param message Notification message
   * @param type Notification type
   * @param options Toast options
   * @returns Promise resolving to the notification ID
   */
  showToast(
    message: string, 
    type?: NotificationType, 
    options?: NotificationOptions
  ): Promise<string>;
  
  /**
   * Show a toast notification with a title
   * @param title Notification title
   * @param message Notification message
   * @param type Notification type
   * @param options Toast options
   * @returns Promise resolving to the notification ID
   */
  showToastWithTitle(
    title: string, 
    message: string, 
    type?: NotificationType, 
    options?: NotificationOptions
  ): Promise<string>;
  
  /**
   * Close a specific toast notification
   * @param id Notification ID
   * @returns Promise that resolves when the notification is closed
   */
  closeToast(id: string): Promise<void>;
  
  /**
   * Close all currently displayed toast notifications
   * @returns Promise that resolves when all notifications are closed
   */
  closeAllToasts(): Promise<void>;
  
  /**
   * Get all notifications for the current user
   * @returns Promise resolving to array of notifications
   */
  getNotifications(): Promise<Notification[]>;
  
  /**
   * Mark a notification as read
   * @param id Notification ID
   * @returns Promise resolving to the updated notification
   */
  markAsRead(id: string): Promise<Notification>;
  
  /**
   * Mark all notifications as read
   * @returns Promise that resolves when all notifications are marked as read
   */
  markAllAsRead(): Promise<void>;
  
  /**
   * Delete a notification
   * @param id Notification ID
   * @returns Promise that resolves when the notification is deleted
   */
  deleteNotification(id: string): Promise<void>;
  
  /**
   * Delete all notifications
   * @returns Promise that resolves when all notifications are deleted
   */
  deleteAllNotifications(): Promise<void>;
  
  /**
   * Get unread notification count
   * @returns Promise resolving to the count of unread notifications
   */
  getUnreadCount(): Promise<number>;
  
  /**
   * Subscribe to new notifications
   * @param callback Function to call when a new notification is received
   * @returns Subscription ID
   */
  subscribeToNotifications(callback: (notification: Notification) => void): string;
  
  /**
   * Unsubscribe from notifications
   * @param subscriptionId Subscription ID
   * @returns Promise that resolves when unsubscribed
   */
  unsubscribeFromNotifications(subscriptionId: string): Promise<void>;
} 