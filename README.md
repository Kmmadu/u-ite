# U-ITE 🔍

**Continuous Network Observability Platform**

[![PyPI version](https://img.shields.io/pypi/v/u-ite.svg)](https://pypi.org/project/u-ite/)
[![Python versions](https://img.shields.io/pypi/pyversions/u-ite.svg)](https://pypi.org/project/u-ite/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://pepy.tech/badge/u-ite)](https://pepy.tech/project/u-ite)

U-ITE (User-Centric Internet Truth Engine) is a powerful, lightweight network observability tool that runs in the background, continuously monitors your internet connection, and provides deep insights into your network performance across multiple ISPs and locations.

![U-ITE Demo](docs/demo.gif)

## ✨ Features

- 🔄 **Continuous Monitoring** - Runs every 30 seconds, automatically detects network changes
- 🌐 **Multi-Network Support** - Tracks different networks separately (home, office, coffee shops, VPNs)
- 📊 **Rich CLI Interface** - 8 powerful command groups for querying and analyzing data
- 📈 **Beautiful Graphs** - Professional NOC-style graphs with dark theme
- 📤 **Data Export** - Export to CSV, JSON, or view as formatted tables
- 🔍 **Smart Event Detection** - Debounced alerts for meaningful events only
- 🏷️ **Network Profiles** - Rename, tag, and organize your networks
- 🔄 **Network Comparison** - Compare performance across different ISPs
- 💾 **SQLite Storage** - Lightweight, portable, no external database needed
- 🖥️ **Cross-Platform** - Works on Linux, macOS, and Windows

## 🚀 Quick Start

### One-Line Install (Linux/macOS)

```bash
curl -sSL https://raw.githubusercontent.com/yourusername/u-ite/main/scripts/install.sh | bash
