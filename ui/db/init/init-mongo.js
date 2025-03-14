db = db.getSiblingDB('kevindb');

db.createUser({
  user: 'kevinuser',
  pwd: 'kevin_password',
  roles: [
    { role: 'readWrite', db: 'kevindb' }
  ]
});

// Create initial collections
db.createCollection('users');
db.createCollection('chatSessions');

// Create example user accounts
db.users.insertMany([
  {
    name: 'Admin User',
    email: 'admin@example.com',
    role: 'admin',
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Student User',
    email: 'student@example.com',
    role: 'student',
    createdAt: new Date(),
    updatedAt: new Date()
  },
  {
    name: 'Parent User',
    email: 'parent@example.com',
    role: 'parent',
    createdAt: new Date(),
    updatedAt: new Date()
  }
]);

// Create some example chat sessions
db.chatSessions.insertMany([
  {
    userId: db.users.findOne({role: 'student'})._id,
    title: 'Math Homework Help',
    messages: [
      {
        role: 'user',
        content: 'Can you help me with algebra?',
        timestamp: new Date()
      },
      {
        role: 'assistant',
        content: 'Of course! I\'d be happy to help with algebra. What specific problem are you working on?',
        timestamp: new Date(new Date().getTime() + 1000)
      }
    ],
    createdAt: new Date(),
    updatedAt: new Date()
  }
]); 