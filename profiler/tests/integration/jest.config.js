module.exports = {
    preset: 'ts-jest',
    testEnvironment: 'jsdom',
    setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
    moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/../../app/ui/src/$1',
    },
    transform: {
        '^.+\\.(ts|tsx)$': ['ts-jest', {
            tsconfig: '../ui/tsconfig.json',
        }],
    },
    testMatch: ['**/*.test.[jt]s?(x)'],
    modulePaths: [
        '<rootDir>/node_modules',
        '<rootDir>/../../app/ui/node_modules',
        '<rootDir>/../ui/node_modules'
    ],
    moduleDirectories: ['node_modules', '../../app/ui/node_modules', '../ui/node_modules']
}; 