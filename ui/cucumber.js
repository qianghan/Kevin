module.exports = {
  default: {
    paths: ['tests/features/**/*.feature'],
    require: ['tests/features/steps/**/*.ts'],
    requireModule: ['ts-node/register'],
    format: ['progress', 'html:reports/cucumber-report.html'],
    parallel: 2
  }
}; 