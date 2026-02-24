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

## [0.2.2] - 2026-02-24
### Fixed
- Additional Python 3.9 compatibility fixes in emitter.py
- All union types (`| None`) replaced with `Optional[]`
- Full Python 3.8-3.12 support now confirmed

## [0.2.4] - 2026-02-24
### Fixed
- Windows packet loss parsing (fixed "Loss: None%" issue)
- Quality verdicts now show correctly (Slow/Degraded/Unstable)
- Windows console encoding for emoji support
- Improved ping output parsing for all platforms

## [0.2.5] - 2026-02-24
### Fixed
- Windows packet loss parsing (fixed "Loss: None%" issue)
- Windows shutdown encoding errors
- Quality verdicts now show correctly (Slow/Degraded/Unstable)
- Enhanced emoji support on all platforms


## [0.2.6] - 2026-02-24
### Fixed
- Final Windows shutdown encoding errors
- Added WindowsSafeHandler for console logging
- Force exit on Windows to ensure clean shutdown
- All emoji issues resolved across all platforms
