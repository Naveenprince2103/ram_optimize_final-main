import argparse
import sys
import time
from rich.console import Console
from rich.table import Table
from .core.config import settings
from .core.logger import logger
from .optimizer.tab_purger import TabPurger
from .vault.manager import get_vault

console = Console()

def cmd_optimize(args):
    """Handle optimize command (Tab Purger)."""
    console.print("[bold blue]RAM Sentinel | Neural Tab-Purger[/bold blue]")
    purger = TabPurger()
    try:
        purger.start_session(headless=not args.visible)
        
        if args.auto:
            while True:
                purger.scan_and_purge(dry_run=args.dry_run)
                if args.once:
                    break
                time.sleep(60)
        else:
            # Single scan
            purger.scan_and_purge(dry_run=args.dry_run)
            
    except KeyboardInterrupt:
        console.print("[yellow]Stopping optimizer...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
    finally:
        purger.stop_session()

def cmd_vault(args):
    """Handle vault command (Ghost Drive)."""
    console.print("[bold green]RAM Sentinel | Ghost Drive[/bold green]")
    vault = get_vault()
    
    if args.panic:
        vault.panic()
        return

    mount_point = args.mount_point or (
        settings.DEFAULT_MOUNT_POINT_WIN if sys.platform == 'win32' else settings.DEFAULT_MOUNT_POINT_UNIX
    )

    if args.mount:
        size = args.size or settings.DEFAULT_VAULT_SIZE
        vault.mount(size, mount_point)
        
    elif args.unmount:
        vault.unmount(mount_point)
        
    else:
        console.print("[yellow]Please specify --mount, --unmount, or --panic[/yellow]")

def cmd_panic(args):
    """System-wide panic."""
    console.print("[bold red]PANIC PROTOCOL INITIATED[/bold red]")
    
    # 1. Purge tabs
    try:
        purger = TabPurger()
        purger.start_session()
        console.print("Closing all tabs...")
        # Close all pages found
        if purger.context:
            for page in purger.context.pages:
                page.close()
        purger.stop_session()
    except Exception as e:
        console.print(f"Purge failed: {e}")

    # 2. Destroy Vault
    try:
        vault = get_vault()
        vault.panic()
    except Exception as e:
        console.print(f"Vault wipe failed: {e}")

def main():
    parser = argparse.ArgumentParser(description="RAM Sentinel - Memory Optimization & Secure Storage")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Optimize Command
    opt_parser = subparsers.add_parser("optimize", help="Monitor and purge browser tabs")
    opt_parser.add_argument("--auto", action="store_true", help="Run in continuous monitoring mode")
    opt_parser.add_argument("--once", action="store_true", help="Run once then exit (used with --auto)")
    opt_parser.add_argument("--dry-run", action="store_true", help="Scan but do not close tabs")
    opt_parser.add_argument("--visible", action="store_true", help="Show browser window")

    # Vault Command
    vault_parser = subparsers.add_parser("vault", help="Manage Ghost Drive")
    vault_parser.add_argument("--mount", action="store_true", help="Mount RAM drive")
    vault_parser.add_argument("--unmount", action="store_true", help="Unmount RAM drive")
    vault_parser.add_argument("--panic", action="store_true", help="Emergency wipe vault")
    vault_parser.add_argument("--size", help="Size of vault (e.g. 500M)")
    vault_parser.add_argument("--mount-point", help="Drive letter (win) or path (unix)")

    # Panic Command
    subparsers.add_parser("panic", help="Emergency system-wide wipe")

    args = parser.parse_args()

    if args.command == "optimize":
        cmd_optimize(args)
    elif args.command == "vault":
        cmd_vault(args)
    elif args.command == "panic":
        cmd_panic(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
