# Changelog

## [0.2.0] - 2026-02-23
### Added
- Complete CLI with 8 command groups
- Network profiling and tagging
- Graph generation with dark theme
- Export functionality (CSV/JSON)
- Network comparison
- Cross-platform service management
- Comprehensive documentation

### Fixed
- All import issues
- Event store integration
- Daemon startup
- Database path handling


## [0.2.1] - 2026-02-24
### Fixed
- Python 3.8-3.9 compatibility (replaced union types with Optional[])
- Cross-platform path resolution for installed packages
- Windows service error handling (no more false success messages)
- Daemon command now works correctly when installed via pip
- Added proper error messages for all platforms

### Changed
- Improved path resolution to work in both development and installed environments
- Better cross-platform log file detection
