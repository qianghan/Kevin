import { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  IRelationshipService, 
  IParentStudentRelationshipService,
  IAdminRelationshipService,
  ITeacherRelationshipViewService,
  Relationship,
  Invitation,
  RelationshipType
} from '@/lib/interfaces/services/relationship.service';
import { User, UserRole } from '@/lib/interfaces/services/user.service';
import { relationshipServiceFactory } from '@/lib/services/relationship/RelationshipServiceFactory';

/**
 * Relationship context type definition
 */
interface RelationshipContextType {
  // State
  relationships: Relationship[];
  invitations: Invitation[];
  linkedStudents: User[];
  isLoading: boolean;
  error: string | null;
  
  // Core relationship functions
  getMyRelationships: () => Promise<Relationship[]>;
  getMyInvitations: () => Promise<Invitation[]>;
  hasRelationshipWith: (userId: string, type?: RelationshipType) => Promise<boolean>;
  createInvitation: (email: string, relationType: RelationshipType, message?: string) => Promise<Invitation>;
  acceptInvitation: (invitationId: string) => Promise<Relationship>;
  rejectInvitation: (invitationId: string) => Promise<boolean>;
  removeRelationship: (relationshipId: string) => Promise<boolean>;
  
  // Parent-student specific functions
  getLinkedStudents: () => Promise<User[]>;
  linkToStudent: (studentEmail: string, message?: string) => Promise<Invitation>;
  getStudentAcademicInfo: (studentId: string) => Promise<any>;
  getStudentProgressReports: (studentId: string) => Promise<any[]>;
  
  // Admin specific functions
  getAllRelationships: (page?: number, limit?: number) => Promise<Relationship[]>;
  getAllInvitations: (page?: number, limit?: number) => Promise<Invitation[]>;
  createRelationship: (fromUserId: string, toUserId: string, relationType: RelationshipType) => Promise<Relationship>;
  updateRelationship: (relationshipId: string, updates: Partial<Relationship>) => Promise<Relationship>;
  deleteRelationship: (relationshipId: string) => Promise<boolean>;
  
  // Teacher specific functions
  getStudentParentRelationships: (studentId: string) => Promise<Relationship[]>;
  getStudentParentContacts: (studentId: string) => Promise<any[]>;
  
  // Utility functions
  refreshRelationships: () => Promise<void>;
  hasParentRole: boolean;
  hasTeacherRole: boolean;
  hasAdminRole: boolean;
}

// Default context value
const defaultContextValue: RelationshipContextType = {
  // State
  relationships: [],
  invitations: [],
  linkedStudents: [],
  isLoading: false,
  error: null,
  
  // Core relationship functions
  getMyRelationships: async () => [],
  getMyInvitations: async () => [],
  hasRelationshipWith: async () => false,
  createInvitation: async () => ({ 
    id: '', 
    fromUserId: '', 
    toUserEmail: '', 
    relationType: RelationshipType.PARENT_STUDENT, 
    status: 'sent' as any, 
    createdAt: '', 
    expiresAt: '' 
  }),
  acceptInvitation: async () => ({ 
    id: '', 
    fromUserId: '', 
    toUserId: '', 
    relationType: RelationshipType.PARENT_STUDENT, 
    status: 'active' as any, 
    createdAt: '', 
    updatedAt: '' 
  }),
  rejectInvitation: async () => false,
  removeRelationship: async () => false,
  
  // Parent-student specific functions
  getLinkedStudents: async () => [],
  linkToStudent: async () => ({ 
    id: '', 
    fromUserId: '', 
    toUserEmail: '', 
    relationType: RelationshipType.PARENT_STUDENT, 
    status: 'sent' as any, 
    createdAt: '', 
    expiresAt: '' 
  }),
  getStudentAcademicInfo: async () => ({}),
  getStudentProgressReports: async () => [],
  
  // Admin specific functions
  getAllRelationships: async () => [],
  getAllInvitations: async () => [],
  createRelationship: async () => ({ 
    id: '', 
    fromUserId: '', 
    toUserId: '', 
    relationType: RelationshipType.PARENT_STUDENT, 
    status: 'active' as any, 
    createdAt: '', 
    updatedAt: '' 
  }),
  updateRelationship: async () => ({ 
    id: '', 
    fromUserId: '', 
    toUserId: '', 
    relationType: RelationshipType.PARENT_STUDENT, 
    status: 'active' as any, 
    createdAt: '', 
    updatedAt: '' 
  }),
  deleteRelationship: async () => false,
  
  // Teacher specific functions
  getStudentParentRelationships: async () => [],
  getStudentParentContacts: async () => [],
  
  // Utility functions
  refreshRelationships: async () => {},
  hasParentRole: false,
  hasTeacherRole: false,
  hasAdminRole: false
};

// Create the context
export const RelationshipContext = createContext<RelationshipContextType>(defaultContextValue);

// Hook to use relationship context
export function useRelationships() {
  const context = useContext(RelationshipContext);
  if (!context) {
    throw new Error('useRelationships must be used within a RelationshipProvider');
  }
  return context;
}

// Hook for managing relationship state
export function useRelationshipState() {
  // State variables
  const [relationships, setRelationships] = useState<Relationship[]>([]);
  const [invitations, setInvitations] = useState<Invitation[]>([]);
  const [linkedStudents, setLinkedStudents] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [userRole, setUserRole] = useState<UserRole | null>(null);
  
  // Get service instances
  const baseService = relationshipServiceFactory.getRelationshipService();
  const parentService = relationshipServiceFactory.getParentStudentService();
  const adminService = relationshipServiceFactory.getAdminService();
  const teacherService = relationshipServiceFactory.getTeacherViewService();
  
  // Helper function to set user role from permissions service
  // In a real implementation, we would get the user's role from the auth service
  const getUserRole = () => {
    // For now, let's assume we're working with a parent role
    setUserRole(UserRole.PARENT);
  };
  
  // Computed properties for role checks
  const hasParentRole = userRole === UserRole.PARENT;
  const hasTeacherRole = userRole === UserRole.TEACHER;
  const hasAdminRole = userRole === UserRole.ADMIN;
  
  // Load initial data
  const loadInitialData = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      
      // Get user role
      getUserRole();
      
      // Load relationships
      const userRelationships = await baseService.getMyRelationships();
      setRelationships(userRelationships);
      
      // Load invitations
      const userInvitations = await baseService.getMyInvitations();
      setInvitations(userInvitations);
      
      // If user is a parent, load linked students
      if (parentService && hasParentRole) {
        const students = await parentService.getLinkedStudents();
        setLinkedStudents(students);
      }
    } catch (err) {
      console.error('Error loading relationship data:', err);
      setError('Failed to load relationship data');
    } finally {
      setIsLoading(false);
    }
  }, [baseService, parentService, hasParentRole]);
  
  // Load data on mount
  useEffect(() => {
    loadInitialData();
  }, [loadInitialData]);
  
  // Core relationship functions
  const getMyRelationships = useCallback(async () => {
    try {
      const result = await baseService.getMyRelationships();
      setRelationships(result);
      return result;
    } catch (err) {
      console.error('Error getting relationships:', err);
      throw err;
    }
  }, [baseService]);
  
  const getMyInvitations = useCallback(async () => {
    try {
      const result = await baseService.getMyInvitations();
      setInvitations(result);
      return result;
    } catch (err) {
      console.error('Error getting invitations:', err);
      throw err;
    }
  }, [baseService]);
  
  const hasRelationshipWith = useCallback(async (userId: string, type?: RelationshipType) => {
    try {
      return await baseService.hasRelationshipWith(userId, type);
    } catch (err) {
      console.error('Error checking relationship:', err);
      throw err;
    }
  }, [baseService]);
  
  const createInvitation = useCallback(async (email: string, relationType: RelationshipType, message?: string) => {
    try {
      const result = await baseService.createInvitation(email, relationType, message);
      // Refresh invitations
      getMyInvitations();
      return result;
    } catch (err) {
      console.error('Error creating invitation:', err);
      throw err;
    }
  }, [baseService, getMyInvitations]);
  
  const acceptInvitation = useCallback(async (invitationId: string) => {
    try {
      const result = await baseService.acceptInvitation(invitationId);
      // Refresh both relationships and invitations
      getMyRelationships();
      getMyInvitations();
      return result;
    } catch (err) {
      console.error('Error accepting invitation:', err);
      throw err;
    }
  }, [baseService, getMyRelationships, getMyInvitations]);
  
  const rejectInvitation = useCallback(async (invitationId: string) => {
    try {
      const result = await baseService.rejectInvitation(invitationId);
      // Refresh invitations
      getMyInvitations();
      return result;
    } catch (err) {
      console.error('Error rejecting invitation:', err);
      throw err;
    }
  }, [baseService, getMyInvitations]);
  
  const removeRelationship = useCallback(async (relationshipId: string) => {
    try {
      const result = await baseService.removeRelationship(relationshipId);
      // Refresh relationships
      getMyRelationships();
      return result;
    } catch (err) {
      console.error('Error removing relationship:', err);
      throw err;
    }
  }, [baseService, getMyRelationships]);
  
  // Parent-specific functions
  const getLinkedStudents = useCallback(async () => {
    if (!parentService) {
      throw new Error('Parent service not available');
    }
    
    try {
      const result = await parentService.getLinkedStudents();
      setLinkedStudents(result);
      return result;
    } catch (err) {
      console.error('Error getting linked students:', err);
      throw err;
    }
  }, [parentService]);
  
  const linkToStudent = useCallback(async (studentEmail: string, message?: string) => {
    if (!parentService) {
      throw new Error('Parent service not available');
    }
    
    try {
      const result = await parentService.linkToStudent(studentEmail, message);
      // Refresh invitations
      getMyInvitations();
      return result;
    } catch (err) {
      console.error('Error linking to student:', err);
      throw err;
    }
  }, [parentService, getMyInvitations]);
  
  const getStudentAcademicInfo = useCallback(async (studentId: string) => {
    if (!parentService) {
      throw new Error('Parent service not available');
    }
    
    try {
      return await parentService.getStudentAcademicInfo(studentId);
    } catch (err) {
      console.error('Error getting student academic info:', err);
      throw err;
    }
  }, [parentService]);
  
  const getStudentProgressReports = useCallback(async (studentId: string) => {
    if (!parentService) {
      throw new Error('Parent service not available');
    }
    
    try {
      return await parentService.getStudentProgressReports(studentId);
    } catch (err) {
      console.error('Error getting student progress reports:', err);
      throw err;
    }
  }, [parentService]);
  
  // Admin-specific functions
  const getAllRelationships = useCallback(async (page?: number, limit?: number) => {
    if (!adminService) {
      throw new Error('Admin service not available');
    }
    
    try {
      return await adminService.getAllRelationships(page, limit);
    } catch (err) {
      console.error('Error getting all relationships:', err);
      throw err;
    }
  }, [adminService]);
  
  const getAllInvitations = useCallback(async (page?: number, limit?: number) => {
    if (!adminService) {
      throw new Error('Admin service not available');
    }
    
    try {
      return await adminService.getAllInvitations(page, limit);
    } catch (err) {
      console.error('Error getting all invitations:', err);
      throw err;
    }
  }, [adminService]);
  
  const createRelationship = useCallback(async (fromUserId: string, toUserId: string, relationType: RelationshipType) => {
    if (!adminService) {
      throw new Error('Admin service not available');
    }
    
    try {
      return await adminService.createRelationship(fromUserId, toUserId, relationType);
    } catch (err) {
      console.error('Error creating relationship:', err);
      throw err;
    }
  }, [adminService]);
  
  const updateRelationship = useCallback(async (relationshipId: string, updates: Partial<Relationship>) => {
    if (!adminService) {
      throw new Error('Admin service not available');
    }
    
    try {
      return await adminService.updateRelationship(relationshipId, updates);
    } catch (err) {
      console.error('Error updating relationship:', err);
      throw err;
    }
  }, [adminService]);
  
  const deleteRelationship = useCallback(async (relationshipId: string) => {
    if (!adminService) {
      throw new Error('Admin service not available');
    }
    
    try {
      return await adminService.deleteRelationship(relationshipId);
    } catch (err) {
      console.error('Error deleting relationship:', err);
      throw err;
    }
  }, [adminService]);
  
  // Teacher-specific functions
  const getStudentParentRelationships = useCallback(async (studentId: string) => {
    if (!teacherService) {
      throw new Error('Teacher service not available');
    }
    
    try {
      return await teacherService.getStudentParentRelationships(studentId);
    } catch (err) {
      console.error('Error getting student parent relationships:', err);
      throw err;
    }
  }, [teacherService]);
  
  const getStudentParentContacts = useCallback(async (studentId: string) => {
    if (!teacherService) {
      throw new Error('Teacher service not available');
    }
    
    try {
      return await teacherService.getStudentParentContacts(studentId);
    } catch (err) {
      console.error('Error getting student parent contacts:', err);
      throw err;
    }
  }, [teacherService]);
  
  // Utility functions
  const refreshRelationships = useCallback(async () => {
    await loadInitialData();
  }, [loadInitialData]);
  
  return {
    // State
    relationships,
    invitations,
    linkedStudents,
    isLoading,
    error,
    
    // Core relationship functions
    getMyRelationships,
    getMyInvitations,
    hasRelationshipWith,
    createInvitation,
    acceptInvitation,
    rejectInvitation,
    removeRelationship,
    
    // Parent-student specific functions
    getLinkedStudents,
    linkToStudent,
    getStudentAcademicInfo,
    getStudentProgressReports,
    
    // Admin specific functions
    getAllRelationships,
    getAllInvitations,
    createRelationship,
    updateRelationship,
    deleteRelationship,
    
    // Teacher specific functions
    getStudentParentRelationships,
    getStudentParentContacts,
    
    // Utility functions
    refreshRelationships,
    hasParentRole,
    hasTeacherRole,
    hasAdminRole
  };
} 