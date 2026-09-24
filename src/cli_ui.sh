#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# cli_ui.sh — UI helper library for MLX-Man
# Sourced by start_llm.sh. Do not execute directly.
# ─────────────────────────────────────────────────────────────────────────────

# ── Version ──────────────────────────────────────────────────────────────────
CLI_VERSION="0.3.0"

# ── ANSI Color & Style Constants ─────────────────────────────────────────────
# Graceful fallback: disable colors if output is not a terminal
if [ -t 1 ] && command -v tput &>/dev/null && [ "$(tput colors 2>/dev/null)" -ge 8 ]; then
    C_RESET="\033[0m"
    C_BOLD="\033[1m"
    C_DIM="\033[2m"
    C_ITALIC="\033[3m"
    C_UNDERLINE="\033[4m"

    C_RED="\033[31m"
    C_GREEN="\033[32m"
    C_YELLOW="\033[33m"
    C_BLUE="\033[34m"
    C_MAGENTA="\033[35m"
    C_CYAN="\033[36m"
    C_WHITE="\033[37m"

    C_BG_RED="\033[41m"
    C_BG_GREEN="\033[42m"
    C_BG_YELLOW="\033[43m"
    C_BG_BLUE="\033[44m"
    C_BG_CYAN="\033[46m"
else
    C_RESET="" C_BOLD="" C_DIM="" C_ITALIC="" C_UNDERLINE=""
    C_RED="" C_GREEN="" C_YELLOW="" C_BLUE="" C_MAGENTA="" C_CYAN="" C_WHITE=""
    C_BG_RED="" C_BG_GREEN="" C_BG_YELLOW="" C_BG_BLUE="" C_BG_CYAN=""
fi

# ── Styled Print Functions ───────────────────────────────────────────────────

header() {
    # Print a section header with a divider
    echo ""
    echo -e "${C_BOLD}${C_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}  $1${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${C_RESET}"
}

subheader() {
    echo ""
    echo -e "${C_BOLD}${C_WHITE}  ── $1 ──${C_RESET}"
}

divider() {
    echo -e "${C_DIM}  ─────────────────────────────────────────────────────────────${C_RESET}"
}

info() {
    echo -e "  ${C_CYAN}ℹ${C_RESET}  $1"
}

success() {
    echo -e "  ${C_GREEN}✔${C_RESET}  $1"
}

warn() {
    echo -e "  ${C_YELLOW}⚠${C_RESET}  ${C_YELLOW}$1${C_RESET}"
}

error() {
    echo -e "  ${C_RED}✖${C_RESET}  ${C_RED}$1${C_RESET}"
}

menu_item() {
    # Usage: menu_item "1" "Run LLM Server" "Start an MLX model as an API server"
    local num="$1" title="$2" desc="$3"
    echo -e "  ${C_BOLD}${C_GREEN}[$num]${C_RESET}  ${C_BOLD}${C_WHITE}$title${C_RESET}"
    if [ -n "$desc" ]; then
        echo -e "       ${C_DIM}$desc${C_RESET}"
    fi
}

label_value() {
    # Usage: label_value "Chip" "Apple M4"
    local label="$1" value="$2"
    printf "  ${C_DIM}%-16s${C_RESET} ${C_WHITE}%s${C_RESET}\n" "$label" "$value"
}

# ── System Information ───────────────────────────────────────────────────────

get_chip_name() {
    sysctl -n machdep.cpu.brand_string 2>/dev/null || echo "Unknown"
}

get_total_ram_gb() {
    local bytes
    bytes=$(sysctl -n hw.memsize 2>/dev/null)
    if [ -n "$bytes" ]; then
        echo $(( bytes / 1024 / 1024 / 1024 ))
    else
        echo "?"
    fi
}

get_free_ram_mb() {
    local pagesize free inactive speculative
    pagesize=$(sysctl -n hw.pagesize 2>/dev/null) || return
    local vm_stat_output
    vm_stat_output=$(vm_stat 2>/dev/null) || return
    free=0; inactive=0; speculative=0
    while IFS= read -r line; do
        case "$line" in
            *"Pages free"*)       free=$(echo "$line" | awk -F: '{gsub(/[^0-9]/,"",$2); print $2}') ;;
            *"Pages inactive"*)   inactive=$(echo "$line" | awk -F: '{gsub(/[^0-9]/,"",$2); print $2}') ;;
            *"Pages speculative"*) speculative=$(echo "$line" | awk -F: '{gsub(/[^0-9]/,"",$2); print $2}') ;;
        esac
    done <<< "$vm_stat_output"
    echo $(( (free + inactive + speculative) * pagesize / 1024 / 1024 ))
}

get_free_ram_display() {
    local mb
    mb=$(get_free_ram_mb)
    if [ -z "$mb" ] || [ "$mb" = "0" ]; then
        echo "Unknown"
    elif [ "$mb" -ge 1024 ]; then
        echo "$(( mb / 1024 )) GB (${mb} MB)"
    else
        echo "${mb} MB"
    fi
}

get_current_gpu_limit() {
    local limit_mb
    limit_mb=$(sysctl -n iogpu.wired_limit_mb 2>/dev/null)
    if [ -n "$limit_mb" ] && [ "$limit_mb" -gt 0 ]; then
        echo "$(( limit_mb / 1024 )) GB"
    else
        echo "Default (~21 GB)"
    fi
}

get_macos_version() {
    sw_vers -productVersion 2>/dev/null || echo "Unknown"
}

# ── Branded Banner ───────────────────────────────────────────────────────────

print_banner() {
    clear
    echo ""
    echo -e "${C_BOLD}${C_CYAN}    ╔═══════════════════════════════════════════════════════╗${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}    ║                                                       ║${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}    ║${C_RESET}${C_BOLD}${C_WHITE}     ⚡  MLX-Man  ⚡                                   ${C_RESET}${C_BOLD}${C_CYAN}║${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}    ║${C_RESET}${C_DIM}        Local MLX LLM Manager for Mac (not an agent)    ${C_RESET}${C_BOLD}${C_CYAN}║${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}    ║                                                       ║${C_RESET}"
    echo -e "${C_BOLD}${C_CYAN}    ╚═══════════════════════════════════════════════════════╝${C_RESET}"
    echo -e "    ${C_DIM}v${CLI_VERSION}${C_RESET}"
    echo ""
}

# ── System Dashboard ─────────────────────────────────────────────────────────

print_system_dashboard() {
    subheader "System Status"
    echo ""
    label_value "Chip"        "$(get_chip_name)"
    label_value "Total RAM"   "$(get_total_ram_gb) GB"
    label_value "Free RAM"    "$(get_free_ram_display)"
    label_value "GPU Limit"   "$(get_current_gpu_limit)"
    label_value "macOS"       "$(get_macos_version)"
    label_value "Date"        "$(date '+%Y-%m-%d %H:%M')"
    echo ""
}

# ── Input Helpers ────────────────────────────────────────────────────────────

prompt_choice() {
    # Usage: prompt_choice "Action" 1 4
    # Reads user input, validates it is a number in [min, max], returns via $REPLY
    local label="$1" min="$2" max="$3"
    while true; do
        echo ""
        echo -ne "  ${C_BOLD}${C_WHITE}${label} [${min}-${max}]:${C_RESET} "
        read -r REPLY
        if [[ "$REPLY" =~ ^[0-9]+$ ]] && [ "$REPLY" -ge "$min" ] && [ "$REPLY" -le "$max" ]; then
            return 0
        fi
        warn "Please enter a number between $min and $max."
    done
}

prompt_yes_no() {
    # Usage: prompt_yes_no "Continue?" && echo "yes" || echo "no"
    local prompt="$1"
    echo -ne "  ${C_BOLD}${C_WHITE}${prompt} (y/N):${C_RESET} "
    read -r REPLY
    [[ "$REPLY" =~ ^[Yy]$ ]]
}

press_enter_to_continue() {
    echo ""
    echo -ne "  ${C_DIM}Press Enter to return to the main menu...${C_RESET}"
    read -r
}
