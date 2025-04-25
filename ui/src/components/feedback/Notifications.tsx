import React, { createContext, useContext, useState, useCallback } from 'react';
import { 
  Box, 
  Flex, 
  Text, 
  CloseButton, 
  VStack, 
  HStack, 
  Badge,
  IconButton, 
  Portal,
  useDisclosure,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerOverlay,
  DrawerContent,
  DrawerCloseButton,
  Divider
} from '@chakra-ui/react';
import { AnimatePresence, motion } from 'framer-motion';

// Notification types
export type NotificationStatus = 'info' | 'success' | 'warning' | 'error';

export interface NotificationProps {
  /**
   * Unique identifier
   */
  id: string;
  /**
   * Notification title
   */
  title: string;
  /**
   * Notification message
   */
  message?: string;
  /**
   * Notification status/severity
   */
  status?: NotificationStatus;
  /**
   * Auto-dismiss duration in ms (0 for no auto-dismiss)
   */
  duration?: number;
  /**
   * Timestamp when notification was created
   */
  timestamp?: Date;
  /**
   * Whether the notification has been read
   */
  isRead?: boolean;
  /**
   * Optional action button text
   */
  actionText?: string;
  /**
   * Optional action callback
   */
  onAction?: () => void;
}

// Context for notifications
interface NotificationContextValue {
  notifications: NotificationProps[];
  show: (notification: Omit<NotificationProps, 'id' | 'timestamp'>) => string;
  update: (id: string, notification: Partial<NotificationProps>) => void;
  remove: (id: string) => void;
  removeAll: () => void;
  markAllAsRead: () => void;
}

const NotificationContext = createContext<NotificationContextValue | undefined>(undefined);

/**
 * Provider component for notifications system
 */
export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [notifications, setNotifications] = useState<NotificationProps[]>([]);
  
  // Add a new notification
  const show = useCallback((notification: Omit<NotificationProps, 'id' | 'timestamp'>) => {
    const id = `notification-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    const newNotification: NotificationProps = {
      ...notification,
      id,
      timestamp: new Date(),
      isRead: false,
      duration: notification.duration ?? (notification.status === 'error' ? 0 : 5000),
    };
    
    setNotifications(current => [...current, newNotification]);
    
    // Auto-dismiss if duration is set
    if (newNotification.duration && newNotification.duration > 0) {
      setTimeout(() => {
        remove(id);
      }, newNotification.duration);
    }
    
    return id;
  }, []);
  
  // Update an existing notification
  const update = useCallback((id: string, notification: Partial<NotificationProps>) => {
    setNotifications(current => 
      current.map(item => 
        item.id === id ? { ...item, ...notification } : item
      )
    );
  }, []);
  
  // Remove a notification
  const remove = useCallback((id: string) => {
    setNotifications(current => current.filter(item => item.id !== id));
  }, []);
  
  // Remove all notifications
  const removeAll = useCallback(() => {
    setNotifications([]);
  }, []);
  
  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    setNotifications(current => 
      current.map(item => ({ ...item, isRead: true }))
    );
  }, []);
  
  const value = {
    notifications,
    show,
    update,
    remove,
    removeAll,
    markAllAsRead,
  };
  
  return (
    <NotificationContext.Provider value={value}>
      {children}
      <ToastContainer />
    </NotificationContext.Provider>
  );
};

/**
 * Hook to access the notification system
 */
export const useNotification = () => {
  const context = useContext(NotificationContext);
  
  if (!context) {
    throw new Error('useNotification must be used within a NotificationProvider');
  }
  
  return context;
};

/**
 * Container component for toast notifications
 */
const ToastContainer: React.FC = () => {
  const { notifications, remove } = useNotification();
  
  // Filter only recent notifications for toast display
  const toastNotifications = notifications
    .filter(n => n.timestamp && (new Date().getTime() - n.timestamp.getTime() < 60000))
    .slice(-5);
  
  return (
    <Portal>
      <Box
        position="fixed"
        top="20px"
        right="20px"
        maxWidth="400px"
        zIndex="toast"
      >
        <AnimatePresence>
          {toastNotifications.map(notification => (
            <motion.div
              key={notification.id}
              initial={{ opacity: 0, y: -20, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 20, scale: 0.8 }}
              transition={{ duration: 0.2 }}
              style={{ marginBottom: '10px' }}
            >
              <Toast notification={notification} onClose={() => remove(notification.id)} />
            </motion.div>
          ))}
        </AnimatePresence>
      </Box>
    </Portal>
  );
};

/**
 * Individual toast notification component
 */
export const Toast: React.FC<{ 
  notification: NotificationProps; 
  onClose: () => void;
}> = ({ notification, onClose }) => {
  const { title, message, status = 'info', actionText, onAction } = notification;
  
  const getStatusColor = (status: NotificationStatus) => {
    switch (status) {
      case 'success': return 'green.500';
      case 'warning': return 'orange.500';
      case 'error': return 'red.500';
      default: return 'blue.500';
    }
  };
  
  const getStatusIcon = (status: NotificationStatus) => {
    switch (status) {
      case 'success': return '✓';
      case 'warning': return '⚠️';
      case 'error': return '✕';
      default: return 'ℹ️';
    }
  };
  
  return (
    <Box
      borderLeft="4px solid"
      borderLeftColor={getStatusColor(status)}
      bg="white"
      boxShadow="md"
      borderRadius="md"
      overflow="hidden"
      role="alert"
      aria-live={status === 'error' ? 'assertive' : 'polite'}
    >
      <Flex>
        <Box p={4} width="100%">
          <Flex alignItems="flex-start" mb={message ? 1 : 0}>
            <Box 
              mr={2}
              color={getStatusColor(status)}
              fontWeight="bold"
              lineHeight="1.2"
              aria-hidden="true"
            >
              {getStatusIcon(status)}
            </Box>
            <Box flex="1">
              <Text fontWeight="bold" fontSize="sm">
                {title}
              </Text>
              {message && (
                <Text fontSize="sm" mt={1} color="gray.600">
                  {message}
                </Text>
              )}
              {actionText && (
                <Box mt={2}>
                  <Text 
                    as="button"
                    fontSize="sm"
                    fontWeight="medium"
                    color={getStatusColor(status)}
                    onClick={() => {
                      onAction?.();
                      onClose();
                    }}
                    _hover={{ textDecoration: 'underline' }}
                  >
                    {actionText}
                  </Text>
                </Box>
              )}
            </Box>
            <CloseButton size="sm" onClick={onClose} />
          </Flex>
        </Box>
      </Flex>
    </Box>
  );
};

/**
 * Notification Center component for displaying all notifications
 */
export const NotificationCenter: React.FC<{
  icon?: React.ReactNode;
  buttonLabel?: string;
}> = ({ 
  icon = '🔔', 
  buttonLabel = 'Notifications'
}) => {
  const { isOpen, onOpen, onClose } = useDisclosure();
  const { notifications, markAllAsRead, removeAll, remove } = useNotification();
  
  const unreadCount = notifications.filter(n => !n.isRead).length;
  
  return (
    <>
      <Box position="relative" display="inline-block">
        <IconButton
          aria-label={buttonLabel}
          icon={<Box>{icon}</Box>}
          onClick={() => {
            onOpen();
            setTimeout(markAllAsRead, 300);
          }}
          variant="ghost"
        />
        {unreadCount > 0 && (
          <Badge
            position="absolute"
            top="-2px"
            right="-2px"
            borderRadius="full"
            bg="red.500"
            color="white"
            fontSize="xs"
            minWidth="18px"
            height="18px"
            textAlign="center"
            lineHeight="18px"
            p={0}
          >
            {unreadCount > 9 ? '9+' : unreadCount}
          </Badge>
        )}
      </Box>
      
      <Drawer isOpen={isOpen} placement="right" onClose={onClose} size="md">
        <DrawerOverlay />
        <DrawerContent>
          <DrawerCloseButton />
          <DrawerHeader borderBottomWidth="1px">
            <Flex justifyContent="space-between" alignItems="center">
              <Text>Notifications</Text>
              {notifications.length > 0 && (
                <Text 
                  as="button"
                  fontSize="sm"
                  color="blue.500"
                  onClick={removeAll}
                  _hover={{ textDecoration: 'underline' }}
                >
                  Clear all
                </Text>
              )}
            </Flex>
          </DrawerHeader>
          <DrawerBody p={0}>
            {notifications.length === 0 ? (
              <Flex 
                height="100%" 
                alignItems="center" 
                justifyContent="center" 
                flexDirection="column"
                p={8}
              >
                <Text fontSize="xl" mb={2}>
                  No notifications
                </Text>
                <Text color="gray.500">
                  You're all caught up!
                </Text>
              </Flex>
            ) : (
              <VStack spacing={0} divider={<Divider />} align="stretch">
                {notifications.map(notification => (
                  <NotificationItem
                    key={notification.id}
                    notification={notification}
                    onClose={() => remove(notification.id)}
                  />
                ))}
              </VStack>
            )}
          </DrawerBody>
        </DrawerContent>
      </Drawer>
    </>
  );
};

/**
 * Individual notification item for the notification center
 */
const NotificationItem: React.FC<{ 
  notification: NotificationProps; 
  onClose: () => void;
}> = ({ notification, onClose }) => {
  const { title, message, status = 'info', timestamp, actionText, onAction } = notification;
  
  const getStatusColor = (status: NotificationStatus) => {
    switch (status) {
      case 'success': return 'green.500';
      case 'warning': return 'orange.500';
      case 'error': return 'red.500';
      default: return 'blue.500';
    }
  };
  
  const getTimeAgo = (date: Date) => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    const diffMin = Math.floor(diffSec / 60);
    const diffHours = Math.floor(diffMin / 60);
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffSec < 60) return 'just now';
    if (diffMin < 60) return `${diffMin}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };
  
  return (
    <Box 
      p={4} 
      _hover={{ bg: 'gray.50' }} 
      borderLeftWidth="4px"
      borderLeftColor={getStatusColor(status)}
    >
      <Flex justifyContent="space-between" mb={1}>
        <Text fontWeight="bold" fontSize="sm">
          {title}
        </Text>
        <HStack spacing={2}>
          {timestamp && (
            <Text fontSize="xs" color="gray.500">
              {getTimeAgo(timestamp)}
            </Text>
          )}
          <CloseButton size="sm" onClick={onClose} />
        </HStack>
      </Flex>
      {message && (
        <Text fontSize="sm" color="gray.600" mb={2}>
          {message}
        </Text>
      )}
      {actionText && (
        <Text 
          as="button"
          fontSize="sm"
          fontWeight="medium"
          color={getStatusColor(status)}
          onClick={onAction}
          _hover={{ textDecoration: 'underline' }}
        >
          {actionText}
        </Text>
      )}
    </Box>
  );
};

export default {
  NotificationProvider,
  useNotification,
  Toast,
  NotificationCenter
}; 