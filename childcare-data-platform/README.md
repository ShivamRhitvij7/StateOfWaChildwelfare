# Childcare Data Platform

This repository contains the Azure Data Factory (ADF) artifacts, CI/CD pipelines, infrastructure as code, and supporting components for the childcare data platform.

## Project Structure

- `adf/` - Azure Data Factory Git-integrated artifacts
- `cicd/` - CI/CD pipeline definitions
- `infra/` - Infrastructure as Code using Bicep
- `arm-template-parameters/` - Environment-specific ARM template parameters
- `sql/` - Database migrations and stored procedures
- `tests/` - Validation and data quality tests
- `docs/` - Documentation

## Getting Started

1. Clone the repository
2. Review the documentation in `docs/`
3. Set up your development environment
4. Run tests: `pytest tests/`

## Deployment

- CI pipeline validates changes on pull requests
- CD pipeline deploys to dev, UAT, and prod environments
- Infrastructure is deployed using Bicep templates

## Contributing

Please read the runbook in `docs/runbook.md` for development and deployment guidelines.