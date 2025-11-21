# Nits - Non Intrusive Test SMTP Server

A simple SMTP server for testing email sending in development environments.

This is a simple SMTP server. It listens for clients sending mails, then stores email into an mbox file and may send notifications to the desktop.

Its purpose is to provide a simple debugging tool for applications sending emails.

Based on the work of Grzegorz Adam Hankiewicz <gradha@efaber.net>

## Features

- Listens for SMTP connections and saves emails to an mbox file
- Optional desktop notifications when emails are received (macOS and Linux)
- Simple command-line interface
- Perfect for development and testing

## Installation

### For users

```bash
pip install nits
```

### For development

```bash
make dev
# or
pip install -e .[dev]
```

## Usage

```bash
# Start with defaults (port 12345)
nits

# Custom port and spool file
nits -p 12345 -s /tmp/spool

# Verbose mode
nits -v

# With desktop notifications
nits -n

# All options combined
nits -p 12345 -s /tmp/spool -v -n
```

## Options

- `-h, --help` - Print help screen
- `-v, --verbose` - Tell when a mail passes
- `-p xxx, --port-number xxx` - Use xxx as port number (default: 12345)
- `-s yyy, --spool-file yyy` - Write mails to this file (default: ~/.fake_spool)
- `-n, --notify` - Send desktop notification when mail passes

## Development

### Building and Publishing

```bash
# Install in development mode
make dev

# Run nits in verbose mode
make run

# Build distribution packages
make release

# Publish to PyPI (requires PyPI credentials)
make publish

# Clean build artifacts
make clean
```

## License

GPL-3.0-or-later

## Author

Jean Schurger <jean@schurger.org>

## Repository

https://github.com/jeansch/nits
