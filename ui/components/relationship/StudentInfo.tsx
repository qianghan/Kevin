'use client';

import { useState, useEffect } from 'react';
import { useRelationships } from '@/hooks/useRelationships';
import { User } from '@/lib/interfaces/services/user.service';

interface StudentInfoProps {
  studentId: string;
  studentName?: string;
}

/**
 * Component for displaying student information to parents
 */
export function StudentInfo({ studentId, studentName }: StudentInfoProps) {
  const { getStudentAcademicInfo, getStudentProgressReports, hasParentRole } = useRelationships();
  
  const [academicInfo, setAcademicInfo] = useState<any>(null);
  const [progressReports, setProgressReports] = useState<any[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  
  useEffect(() => {
    const loadStudentData = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        // Load academic information
        const info = await getStudentAcademicInfo(studentId);
        setAcademicInfo(info);
        
        // Load progress reports
        const reports = await getStudentProgressReports(studentId);
        setProgressReports(reports);
      } catch (err) {
        console.error('Error loading student data:', err);
        setError('Failed to load student information');
      } finally {
        setIsLoading(false);
      }
    };
    
    if (studentId) {
      loadStudentData();
    }
  }, [studentId, getStudentAcademicInfo, getStudentProgressReports]);
  
  if (!hasParentRole) {
    return (
      <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">
        <p className="text-yellow-700">
          Only parents can view student information.
        </p>
      </div>
    );
  }
  
  if (isLoading) {
    return <div className="p-4">Loading student information...</div>;
  }
  
  if (error) {
    return (
      <div className="bg-red-50 border-l-4 border-red-400 p-4 mb-4">
        <p className="text-red-700">{error}</p>
      </div>
    );
  }
  
  return (
    <div className="space-y-8">
      <div className="border rounded-lg overflow-hidden shadow-sm">
        <div className="bg-blue-50 p-4 border-b">
          <h2 className="text-xl font-semibold text-blue-800">
            {studentName || 'Student'} Academic Information
          </h2>
        </div>
        
        {academicInfo && (
          <div className="p-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
              <div>
                <p className="text-sm text-gray-500">GPA</p>
                <p className="text-lg font-medium">{academicInfo.gpa}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">Current Grade</p>
                <p className="text-lg font-medium">{academicInfo.currentGrade}</p>
              </div>
            </div>
            
            <h3 className="text-lg font-medium mb-3">Courses</h3>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Course</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Grade</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Teacher</th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {academicInfo.courses.map((course: any, index: number) => (
                    <tr key={index}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{course.name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                          course.grade.startsWith('A') ? 'bg-green-100 text-green-800' :
                          course.grade.startsWith('B') ? 'bg-blue-100 text-blue-800' :
                          course.grade.startsWith('C') ? 'bg-yellow-100 text-yellow-800' :
                          'bg-red-100 text-red-800'
                        }`}>
                          {course.grade}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{course.teacher}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            
            <p className="text-sm text-gray-500 mt-4">
              Last updated: {new Date(academicInfo.lastUpdated).toLocaleDateString()}
            </p>
          </div>
        )}
      </div>
      
      <div className="border rounded-lg overflow-hidden shadow-sm">
        <div className="bg-blue-50 p-4 border-b">
          <h2 className="text-xl font-semibold text-blue-800">Progress Reports</h2>
        </div>
        
        <div className="p-4">
          {progressReports.length > 0 ? (
            <ul className="divide-y divide-gray-200">
              {progressReports.map((report) => (
                <li key={report.id} className="py-4">
                  <div className="flex items-start">
                    <div className="flex-1">
                      <h3 className="text-lg font-medium text-gray-900">{report.title}</h3>
                      <p className="text-sm text-gray-500">
                        {new Date(report.date).toLocaleDateString()}
                      </p>
                      <p className="mt-2 text-gray-700">{report.comments}</p>
                      
                      {report.attachmentUrl && (
                        <a 
                          href={report.attachmentUrl} 
                          target="_blank" 
                          rel="noopener noreferrer" 
                          className="inline-flex items-center mt-3 text-sm text-blue-600 hover:text-blue-800"
                        >
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M6 2a2 2 0 00-2 2v12a2 2 0 002 2h8a2 2 0 002-2V7.414A2 2 0 0015.414 6L12 2.586A2 2 0 0010.586 2H6zm5 6a1 1 0 10-2 0v3.586l-1.293-1.293a1 1 0 10-1.414 1.414l3 3a1 1 0 001.414 0l3-3a1 1 0 00-1.414-1.414L11 11.586V8z" clipRule="evenodd" />
                          </svg>
                          Download Report
                        </a>
                      )}
                    </div>
                  </div>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-gray-500">No progress reports available.</p>
          )}
        </div>
      </div>
    </div>
  );
} 