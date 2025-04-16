// React testing setup
const React = require('react');
global.React = React;

require('@testing-library/jest-dom');

// Mock WebSocket
class MockWebSocket {
    constructor(url) {
        this.url = url;
        this.readyState = WebSocket.OPEN;
        this.onopen = null;
        this.onmessage = null;
        this.onerror = null;
        this.onclose = null;
        this.messages = [];
        this.sentMessages = [];
    }

    send(data) {
        this.sentMessages.push(data);
    }

    close() {
        this.readyState = WebSocket.CLOSED;
        if (this.onclose) this.onclose();
    }

    mockMessage(data) {
        if (this.onmessage) {
            this.onmessage({ data: JSON.stringify(data) });
        }
    }

    mockError(error) {
        if (this.onerror) {
            this.onerror(error);
        }
    }
}

global.WebSocket = MockWebSocket;

// Mock TextEncoder/TextDecoder
global.TextEncoder = class TextEncoder {
    encode(str) {
        return new Uint8Array(str.split('').map(c => c.charCodeAt(0)));
    }
};

global.TextDecoder = class TextDecoder {
    decode(bytes) {
        return String.fromCharCode.apply(null, bytes);
    }
};

// Mock window.matchMedia
Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: jest.fn().mockImplementation(query => ({
        matches: false,
        media: query,
        onchange: null,
        addListener: jest.fn(),
        removeListener: jest.fn(),
        addEventListener: jest.fn(),
        removeEventListener: jest.fn(),
        dispatchEvent: jest.fn(),
    })),
});

// Mock ResizeObserver
global.ResizeObserver = class ResizeObserver {
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Mock IntersectionObserver
global.IntersectionObserver = class IntersectionObserver {
    constructor() {}
    observe() {}
    unobserve() {}
    disconnect() {}
};

// Mock fetch
global.fetch = jest.fn(() =>
    Promise.resolve({
        json: () => Promise.resolve({}),
        ok: true,
        status: 200,
    })
);

// Mock localStorage
const localStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    clear: jest.fn(),
    removeItem: jest.fn(),
    length: 0,
    key: jest.fn(),
};

global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
    getItem: jest.fn(),
    setItem: jest.fn(),
    clear: jest.fn(),
    removeItem: jest.fn(),
    length: 0,
    key: jest.fn(),
};

global.sessionStorage = sessionStorageMock;

// Mock requestAnimationFrame
global.requestAnimationFrame = callback => setTimeout(callback, 0);
global.cancelAnimationFrame = id => clearTimeout(id);

// Mock performance
global.performance = {
    now: jest.fn(),
    mark: jest.fn(),
    measure: jest.fn(),
    clearMarks: jest.fn(),
    clearMeasures: jest.fn(),
    getEntriesByName: jest.fn(),
    getEntriesByType: jest.fn(),
    getEntries: jest.fn(),
};

// Mock crypto
global.crypto = {
    getRandomValues: jest.fn(),
    subtle: {
        digest: jest.fn(),
        encrypt: jest.fn(),
        decrypt: jest.fn(),
        sign: jest.fn(),
        verify: jest.fn(),
        generateKey: jest.fn(),
        deriveKey: jest.fn(),
        deriveBits: jest.fn(),
        importKey: jest.fn(),
        exportKey: jest.fn(),
        wrapKey: jest.fn(),
        unwrapKey: jest.fn(),
    },
}; 