module.exports = {
  default: {
    paths: ['tests/features/**/*.feature'],
    require: ['tests/steps/**/*.ts'],
    requireModule: ['ts-node/register'],
    format: ['progress', 'html:reports/cucumber-report.html']
  }
}; 