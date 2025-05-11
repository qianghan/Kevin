'use client';

import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { PermissionProvider } from '@/components/permission/PermissionProvider';
import { RoleManagement } from '@/components/permission/RoleManagement';
import { PermissionMatrix } from '@/components/permission/PermissionMatrix';
import { PermissionGuard } from '@/components/permission/PermissionGuard';
import { AccessDenied } from '@/components/permission/AccessDenied';
import { UserRole } from '@/lib/interfaces/services/user.service';

export default function PermissionsPage() {
  return (
    <PermissionProvider>
      <div className="container mx-auto py-8">
        <h1 className="text-3xl font-bold mb-8">Permission Management</h1>
        
        <PermissionGuard
          roles={[UserRole.ADMIN]}
          fallback={<AccessDenied message="Only administrators can access this page." />}
        >
          <Tabs defaultValue="roles" className="w-full">
            <TabsList className="mb-6">
              <TabsTrigger value="roles">Role Management</TabsTrigger>
              <TabsTrigger value="matrix">Permission Matrix</TabsTrigger>
            </TabsList>
            
            <TabsContent value="roles" className="space-y-8">
              <RoleManagement />
            </TabsContent>
            
            <TabsContent value="matrix">
              <PermissionMatrix />
            </TabsContent>
          </Tabs>
        </PermissionGuard>
      </div>
    </PermissionProvider>
  );
} 