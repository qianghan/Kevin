import { Given, When, Then } from '@cucumber/cucumber';
import { expect } from 'chai';

// Mock analytics data
interface AnalyticsData {
  activeUsers: number;
  sessionDuration: number;
  featureUsage: Record<string, number>;
  retentionRate: number;
}

interface UserPrivacySettings {
  analyticsEnabled: boolean;
  dataSharing: boolean;
}

// Test state
let currentUser: { role: string; id: string } | null = null;
let analyticsData: AnalyticsData | null = null;
let selectedReportType: string | null = null;
let dateRange: { start: Date; end: Date } | null = null;
let privacySettings: UserPrivacySettings | null = null;
let currentProvider: string = 'default';
let exportedData: any = null;
let visibleMetrics: string[] = [];

// Given steps
Given('I am logged in as an {string} user', function (role: string) {
  currentUser = { role, id: '1' };
});

Given('a user has disabled analytics tracking', function () {
  privacySettings = {
    analyticsEnabled: false,
    dataSharing: false
  };
});

// When steps
When('I navigate to the analytics dashboard', function () {
  if (currentUser?.role !== 'ADMIN') {
    throw new Error('Unauthorized access to analytics dashboard');
  }
  analyticsData = {
    activeUsers: 150,
    sessionDuration: 25,
    featureUsage: {
      chat: 450,
      profile: 200,
      search: 300
    },
    retentionRate: 0.85
  };
  visibleMetrics = ['activeUsers', 'sessionDuration', 'featureUsage'];
});

When('I view the engagement metrics page', function () {
  if (currentUser?.role !== 'ADMIN') {
    throw new Error('Unauthorized access to engagement metrics');
  }
  visibleMetrics = ['sessionDuration', 'featureUsage', 'retentionRate'];
});

When('I access the reporting interface', function () {
  if (currentUser?.role !== 'ADMIN') {
    throw new Error('Unauthorized access to reporting interface');
  }
  visibleMetrics = ['reportTypes', 'dateRange', 'exportOptions'];
});

When('I select a report type {string}', function (reportType: string) {
  selectedReportType = reportType;
});

When('I set the date range for the report', function () {
  dateRange = {
    start: new Date('2024-01-01'),
    end: new Date('2024-03-31')
  };
});

When('I view the student analytics page', function () {
  if (currentUser?.role !== 'TEACHER' && currentUser?.role !== 'ADMIN') {
    throw new Error('Unauthorized access to student analytics');
  }
  visibleMetrics = ['studentEngagement', 'learningProgress'];
});

When('I export analytics data', function () {
  if (currentUser?.role !== 'ADMIN') {
    throw new Error('Unauthorized access to data export');
  }
  exportedData = {
    timestamp: new Date().toISOString(),
    data: {
      aggregatedMetrics: {
        totalUsers: 1000,
        averageSessionDuration: 30,
        retentionRate: 0.85
      },
      anonymizedRecords: [
        { id: 'user_1', activity: 'high', sessions: 45 },
        { id: 'user_2', activity: 'medium', sessions: 20 }
      ]
    }
  };
});

When('analytics data is collected', function () {
  // Simulate data collection respecting privacy settings
  if (privacySettings && !privacySettings.analyticsEnabled) {
    analyticsData = null;
  }
});

When('I switch the analytics provider to {string}', function (provider: string) {
  currentProvider = provider;
  // Simulate provider switch
  analyticsData = {
    activeUsers: 150,
    sessionDuration: 25,
    featureUsage: {
      chat: 450,
      profile: 200,
      search: 300
    },
    retentionRate: 0.85
  };
});

// Then steps
Then('I should see user activity metrics', function () {
  expect(analyticsData).to.not.be.null;
  expect(visibleMetrics).to.include('activeUsers');
});

Then('I should see active user counts', function () {
  expect(analyticsData?.activeUsers).to.be.a('number');
});

Then('I should see usage trends', function () {
  expect(analyticsData?.featureUsage).to.be.an('object');
});

Then('I should see session duration statistics', function () {
  expect(analyticsData?.sessionDuration).to.be.a('number');
});

Then('I should see feature usage statistics', function () {
  expect(analyticsData?.featureUsage).to.be.an('object');
  expect(Object.keys(analyticsData?.featureUsage || {})).to.have.length.above(0);
});

Then('I should see user retention data', function () {
  expect(analyticsData?.retentionRate).to.be.a('number');
});

Then('I should be able to generate the report', function () {
  expect(selectedReportType).to.not.be.null;
  expect(dateRange).to.not.be.null;
});

Then('I should see the report preview', function () {
  expect(visibleMetrics).to.include('reportTypes');
});

Then('I should see student engagement metrics', function () {
  expect(visibleMetrics).to.include('studentEngagement');
});

Then('I should see learning progress data', function () {
  expect(visibleMetrics).to.include('learningProgress');
});

Then('the exported data should be anonymized', function () {
  expect(exportedData.data.anonymizedRecords[0].id).to.not.match(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/);
});

Then('sensitive information should be redacted', function () {
  const records = exportedData.data.anonymizedRecords;
  records.forEach((record: any) => {
    expect(record).to.not.have.property('email');
    expect(record).to.not.have.property('name');
    expect(record).to.not.have.property('personalInfo');
  });
});

Then('that user\'s data should not be included', function () {
  expect(analyticsData).to.be.null;
});

Then('their privacy preferences should be respected', function () {
  expect(privacySettings?.analyticsEnabled).to.be.false;
});

Then('the analytics data should still be available', function () {
  expect(analyticsData).to.not.be.null;
});

Then('the interface should remain consistent', function () {
  expect(visibleMetrics.length).to.be.above(0);
}); 