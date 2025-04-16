'use client';

import { ProfileProvider, useProfile } from '../context/ProfileContext';

export const ProfileContent = () => {
    const { profileState, loading, error } = useProfile();

    if (loading || !profileState) {
        return <div>Loading...</div>;
    }

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <div className="mb-4">
                <h2 className="text-lg font-semibold">Profile Status</h2>
                <p className="text-gray-600">Status: {profileState.status}</p>
                <p className="text-gray-600">Progress: {profileState.progress}%</p>
            </div>

            {error && (
                <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                    Error: {error}
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
    );
};

// Standalone page that can be tested directly without the provider
export const HomeContent = () => {
    return (
        <main className="min-h-screen p-8">
            <h1 className="text-2xl font-bold mb-4">Student Profile Builder</h1>
            <ProfileContent />
        </main>
    );
};

// Default export with provider for actual app usage
export default function Home() {
    return (
        <ProfileProvider userId="test-user-1">
            <HomeContent />
        </ProfileProvider>
    );
} 