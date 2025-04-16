module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/../../../app/ui/src/$1',
    },
    transform: {
        '^.+\\.(ts|tsx)$': ['ts-jest', {
            tsconfig: 'tsconfig.json',
        }],
    },
    testMatch: ['**/__tests__/**/*.test.[jt]s?(x)'],
    globals: {
        'ts-jest': {
            tsconfig: 'tsconfig.json',
        },
    },
}; 