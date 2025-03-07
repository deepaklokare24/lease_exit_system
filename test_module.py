import asyncio
import logging
import sys
from datetime import datetime
from utils.test_connections import test_all_connections
from utils.test_tasks import verify_task_system
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# Configure rich console
console = Console()

# Configure logging with rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(rich_tracebacks=True)]
)

logger = logging.getLogger("test_module")

async def run_system_tests():
    """Run all system tests and display results"""
    console.print("\n[bold blue]Starting System Tests...[/bold blue]")
    console.print("=" * 50)
    
    start_time = datetime.now()
    
    # Test Connections
    console.print("\n[bold cyan]Testing System Connections[/bold cyan]")
    connection_results = await test_all_connections()
    
    # Create results table
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Component", style="dim")
    table.add_column("Status", justify="center")
    
    for component, status in connection_results.items():
        status_str = "[green]✓ PASS[/green]" if status else "[red]✗ FAIL[/red]"
        table.add_row(component, status_str)
    
    console.print(table)
    
    # Test Task System
    console.print("\n[bold cyan]Testing Task System[/bold cyan]")
    task_result = verify_task_system()
    
    task_table = Table(show_header=True, header_style="bold magenta")
    task_table.add_column("Test", style="dim")
    task_table.add_column("Status", justify="center")
    
    task_status = "[green]✓ PASS[/green]" if task_result else "[red]✗ FAIL[/red]"
    task_table.add_row("Task System", task_status)
    
    console.print(task_table)
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    console.print("\n[bold cyan]Test Summary[/bold cyan]")
    summary_table = Table(show_header=True, header_style="bold magenta")
    summary_table.add_column("Metric", style="dim")
    summary_table.add_column("Value", justify="right")
    
    total_tests = len(connection_results) + 1
    passed_tests = sum(1 for status in connection_results.values() if status) + (1 if task_result else 0)
    
    summary_table.add_row("Total Tests", str(total_tests))
    summary_table.add_row("Passed", str(passed_tests))
    summary_table.add_row("Failed", str(total_tests - passed_tests))
    summary_table.add_row("Duration", f"{duration:.2f}s")
    
    console.print(summary_table)
    
    # Final Status
    all_passed = all(connection_results.values()) and task_result
    status_color = "green" if all_passed else "red"
    status_symbol = "✓" if all_passed else "✗"
    
    console.print(f"\n[bold {status_color}]{status_symbol} Overall Status: {'PASS' if all_passed else 'FAIL'}[/bold {status_color}]")
    
    return all_passed

def main():
    """Main entry point for test module"""
    try:
        # Run tests
        success = asyncio.run(run_system_tests())
        
        # Exit with appropriate status code
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Tests interrupted by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n[red]Error running tests: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main() 