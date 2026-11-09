//! Local executable identity: preserve the upstream `obscura` command while
//! presenting the GoreeCloud product name for the new binary.
//! Kept dependency-free so the name decision can be tested without running
//! upstream build scripts, the network, or V8.

use std::ffi::OsStr;
use std::path::Path;

pub const GOREECLOUD_COMMAND: &str = "goreecloud-headless-browser";
pub const OBSCURA_COMMAND: &str = "obscura";

/// Resolve a static clap command name from the user's invocation.
pub fn command_name(invocation: &OsStr) -> &'static str {
    let file = Path::new(invocation)
        .file_name()
        .and_then(OsStr::to_str)
        .unwrap_or_default();

    if file.eq_ignore_ascii_case(OBSCURA_COMMAND) || file.eq_ignore_ascii_case("obscura.exe") {
        OBSCURA_COMMAND
    } else {
        GOREECLOUD_COMMAND
    }
}

/// A human-readable product identity for the startup banner.
pub fn display_name(command: &str) -> &'static str {
    if command == OBSCURA_COMMAND {
        "Obscura (GoreeCloud compatibility command)"
    } else {
        "GoreeCloud Headless Browser"
    }
}

#[cfg(test)]
mod tests {
    use super::{command_name, display_name, GOREECLOUD_COMMAND, OBSCURA_COMMAND};
    use std::ffi::OsStr;

    #[test]
    fn upstream_binary_retains_upstream_name() {
        assert_eq!(command_name(OsStr::new("obscura")), OBSCURA_COMMAND);
        assert_eq!(command_name(OsStr::new("/usr/local/bin/obscura")), OBSCURA_COMMAND);
        assert_eq!(command_name(OsStr::new("Obscura.EXE")), OBSCURA_COMMAND);
    }

    #[test]
    fn goreecloud_binary_uses_new_product_name() {
        assert_eq!(command_name(OsStr::new(GOREECLOUD_COMMAND)), GOREECLOUD_COMMAND);
        assert_eq!(command_name(OsStr::new("goreecloud-headless-browser.exe")), GOREECLOUD_COMMAND);
    }

    #[test]
    fn unknown_invocations_prefer_the_goreecloud_identity() {
        assert_eq!(command_name(OsStr::new("custom-wrapper")), GOREECLOUD_COMMAND);
        assert_eq!(command_name(OsStr::new("")), GOREECLOUD_COMMAND);
    }

    #[test]
    fn startup_labels_follow_the_invoked_command() {
        assert!(display_name(OBSCURA_COMMAND).starts_with("Obscura"));
        assert_eq!(display_name(GOREECLOUD_COMMAND), "GoreeCloud Headless Browser");
    }
}
