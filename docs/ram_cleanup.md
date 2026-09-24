# RAM Cleanup Safety Classification System

The RAM Cleanup tool includes a safety heuristic classifier to ensure users do not accidentally terminate essential macOS background processes or core ui managers, which can result in system instability.

## Safety Tiers

Processes are classified into one of three safety tiers:

### 1. 🟢 Safe (`[SAFE]`)
These are user applications, development tools, cache workers, or standalone helper tools. Terminating them is generally harmless and will not cause system instability.
**Examples**: `language_server`, `MTLCompilerService`, `Safari`, `VS Code`, `Docker Desktop`.

### 2. 🟡 Caution (`[CAUTION]`)
These are non-essential Apple background services or features. If closed, they will usually restart automatically or cause minor UI disruptions, but will not crash the core system session.
**Examples**: `Siri AI`, `AppleSpell`, `com.apple.weather.menu`, `cloudphotod`.

### 3. 🔴 Critical / Protected (`[DANGEROUS]`)
These are essential macOS core daemons and UI managers. Terminating these could crash the user session, cause data corruption, or lead to immediate system instability. The tool prohibits terminating these processes unless the user explicitly toggles an override flag (`--expert`).
**Examples**: `ControlCenter`, `NotificationCenter`, `cloudd`, `sharingd`, `routined`, `WindowServer`.

## Process Lookup Rules

The classification is performed using a known signature dictionary inside the `ProcessClassifier` class.
- The matcher attempts an exact or substring match against the process name.
- It checks for `DANGER_PROCESSES` first, followed by `SAFE_PROCESSES`, and finally `CAUTION_PROCESSES`.
- **Safe Fallback**: Any unknown process is classified as `Caution` by default. This ensures that random background processes are not immediately flagged as safely terminable or overly restricted, instead requiring user review before termination.
