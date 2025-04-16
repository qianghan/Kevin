'use client';

import { useEffect, useState } from 'react';
import { ProfileService, ProfileState } from '../services/profile';

export default function Home() {
    const [profileState, setProfileState] = useState<ProfileState | null>(null);
    const [profileService, setProfileService] = useState<ProfileService | null>(null);

    useEffect(() => {
        // Initialize profile service with a test user ID
        const service = new ProfileService('test-user-1');
        setProfileService(service);

        // Set up state change handler
        service.onStateChange((state) => {
            setProfileState(state);
        });

        // Connect to WebSocket
        service.connect();

        // Cleanup on unmount
        return () => {
            service.disconnect();
        };
    }, []);

    if (!profileState) {
        return <div>Loading...</div>;
    }

    return (
        <main className="min-h-screen p-8">
            <h1 className="text-2xl font-bold mb-4">Student Profile Builder</h1>
            
            <div className="bg-white rounded-lg shadow p-6">
                <div className="mb-4">
                    <h2 className="text-lg font-semibold">Profile Status</h2>
                    <p className="text-gray-600">Status: {profileState.status}</p>
                    <p className="text-gray-600">Progress: {profileState.progress}%</p>
                </div>

                {profileState.error && (
                    <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                        Error: {profileState.error}
                    </div>
                )}

                {profileState.data && (
                    <div className="mt-4">
                        <h2 className="text-lg font-semibold mb-2">Profile Data</h2>
                        <pre className="bg-gray-100 p-4 rounded overflow-auto">
                            {JSON.stringify(profileState.data, null, 2)}
                        </pre>
                    </div>
                )}
            </div>
        </main>
    );
} 