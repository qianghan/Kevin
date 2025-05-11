'use client';

import { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { RelationshipProvider } from '@/components/relationship/RelationshipProvider';
import { LinkToStudent } from '@/components/relationship/LinkToStudent';
import { StudentInfo } from '@/components/relationship/StudentInfo';
import { useRelationships } from '@/hooks/useRelationships';
import { User } from '@/lib/interfaces/services/user.service';
import { Invitation, Relationship } from '@/lib/interfaces/services/relationship.service';

function RelationshipManagementContent() {
  const { 
    relationships, 
    invitations, 
    linkedStudents, 
    isLoading, 
    error,
    getMyRelationships,
    getMyInvitations,
    acceptInvitation,
    rejectInvitation,
    removeRelationship,
    refreshRelationships
  } = useRelationships();
  
  const [selectedStudentId, setSelectedStudentId] = useState<string | null>(null);
  
  // Load data on mount
  useEffect(() => {
    refreshRelationships();
  }, [refreshRelationships]);
  
  const handleAcceptInvitation = async (invitationId: string) => {
    try {
      await acceptInvitation(invitationId);
      refreshRelationships();
    } catch (err) {
      console.error('Error accepting invitation:', err);
    }
  };
  
  const handleRejectInvitation = async (invitationId: string) => {
    try {
      await rejectInvitation(invitationId);
      refreshRelationships();
    } catch (err) {
      console.error('Error rejecting invitation:', err);
    }
  };
  
  const handleRemoveRelationship = async (relationshipId: string) => {
    if (window.confirm('Are you sure you want to remove this relationship?')) {
      try {
        await removeRelationship(relationshipId);
        refreshRelationships();
        
        // Reset selected student if it was removed
        const relationship = relationships.find(rel => rel.id === relationshipId);
        if (relationship && relationship.toUserId === selectedStudentId) {
          setSelectedStudentId(null);
        }
      } catch (err) {
        console.error('Error removing relationship:', err);
      }
    }
  };
  
  if (isLoading) {
    return <div className="py-8 text-center">Loading relationship data...</div>;
  }
  
  if (error) {
    return (
      <div className="py-8">
        <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
          <p className="text-red-700">{error}</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="py-6">
      <Tabs defaultValue="students" className="w-full">
        <TabsList className="mb-8">
          <TabsTrigger value="students">My Students</TabsTrigger>
          <TabsTrigger value="invitations">Invitations</TabsTrigger>
          <TabsTrigger value="link">Link to Student</TabsTrigger>
        </TabsList>
        
        <TabsContent value="students" className="space-y-6">
          {linkedStudents.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="md:col-span-1 bg-white rounded-lg shadow p-4">
                <h3 className="font-medium text-lg mb-4">Linked Students</h3>
                <ul className="space-y-2">
                  {linkedStudents.map(student => (
                    <li key={student.id}>
                      <button
                        onClick={() => setSelectedStudentId(student.id)}
                        className={`w-full text-left px-4 py-2 rounded-md flex items-center justify-between ${
                          selectedStudentId === student.id
                            ? 'bg-blue-50 text-blue-700'
                            : 'hover:bg-gray-50'
                        }`}
                      >
                        <span>
                          {student.firstName} {student.lastName}
                        </span>
                        {selectedStudentId === student.id && (
                          <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        )}
                      </button>
                    </li>
                  ))}
                </ul>
                
                {relationships.length > 0 && (
                  <div className="mt-6">
                    <h3 className="font-medium text-lg mb-2">Manage Relationships</h3>
                    <ul className="divide-y divide-gray-200">
                      {relationships.map(rel => {
                        const student = linkedStudents.find(s => s.id === rel.toUserId);
                        if (!student) return null;
                        
                        return (
                          <li key={rel.id} className="py-3">
                            <div className="flex items-center justify-between">
                              <span className="text-sm">
                                {student.firstName} {student.lastName}
                              </span>
                              <button 
                                onClick={() => handleRemoveRelationship(rel.id)}
                                className="text-red-600 hover:text-red-800 text-sm"
                              >
                                Remove
                              </button>
                            </div>
                          </li>
                        );
                      })}
                    </ul>
                  </div>
                )}
              </div>
              
              <div className="md:col-span-2">
                {selectedStudentId ? (
                  <StudentInfo 
                    studentId={selectedStudentId} 
                    studentName={linkedStudents.find(s => s.id === selectedStudentId)?.firstName}
                  />
                ) : (
                  <div className="bg-white rounded-lg shadow p-6 text-center">
                    <p className="text-gray-500">
                      Select a student to view their information
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">
                You don't have any linked students yet. Use the "Link to Student" tab to connect with a student.
              </p>
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="invitations" className="space-y-6">
          {invitations.length > 0 ? (
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <ul className="divide-y divide-gray-200">
                {invitations.map(invitation => (
                  <li key={invitation.id} className="p-4">
                    <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
                      <div className="mb-2 sm:mb-0">
                        <p className="font-medium">
                          {invitation.status === 'sent' ? (
                            <>Invitation to <span className="text-blue-600">{invitation.toUserEmail}</span></>
                          ) : (
                            <>Invitation from {invitation.fromUserId}</>
                          )}
                        </p>
                        <p className="text-sm text-gray-500">
                          Sent: {new Date(invitation.createdAt).toLocaleDateString()}
                        </p>
                        <p className="text-sm text-gray-500">
                          Expires: {new Date(invitation.expiresAt).toLocaleDateString()}
                        </p>
                        {invitation.message && (
                          <p className="mt-1 text-gray-700">{invitation.message}</p>
                        )}
                      </div>
                      
                      <div className="flex space-x-2">
                        {invitation.status === 'sent' && invitation.fromUserId !== 'me' ? (
                          <>
                            <button
                              onClick={() => handleAcceptInvitation(invitation.id)}
                              className="px-3 py-1 bg-green-100 text-green-800 rounded-md text-sm font-medium hover:bg-green-200"
                            >
                              Accept
                            </button>
                            <button
                              onClick={() => handleRejectInvitation(invitation.id)}
                              className="px-3 py-1 bg-red-100 text-red-800 rounded-md text-sm font-medium hover:bg-red-200"
                            >
                              Reject
                            </button>
                          </>
                        ) : (
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            invitation.status === 'sent' ? 'bg-yellow-100 text-yellow-800' :
                            invitation.status === 'accepted' ? 'bg-green-100 text-green-800' :
                            invitation.status === 'rejected' ? 'bg-red-100 text-red-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {invitation.status.charAt(0).toUpperCase() + invitation.status.slice(1)}
                          </span>
                        )}
                      </div>
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow p-6 text-center">
              <p className="text-gray-500">
                You don't have any invitations.
              </p>
            </div>
          )}
        </TabsContent>
        
        <TabsContent value="link">
          <LinkToStudent />
        </TabsContent>
      </Tabs>
    </div>
  );
}

export default function RelationshipsPage() {
  return (
    <RelationshipProvider>
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-6">Relationship Management</h1>
        <p className="text-gray-600 mb-8">
          Manage your connections with students and view their academic information.
        </p>
        
        <RelationshipManagementContent />
      </div>
    </RelationshipProvider>
  );
} 