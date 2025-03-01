#!/usr/bin/env python3
"""
Test script to verify subprocess functionality.
"""

import subprocess
import sys
import time

def run_direct_command():
    """Run a command directly that should print to stdout."""
    print("\n1. RUNNING DIRECT COMMAND (should see output):")
    
    # Simple Python command that prints to stdout
    subprocess.run([sys.executable, "-c", "print('Direct command stdout output')"])
    
    # Simple Python command that prints to stderr
    subprocess.run([sys.executable, "-c", "import sys; print('Direct command stderr output', file=sys.stderr)"])
    
    print("Direct command completed\n")

def run_captured_command():
    """Run a command with capture_output=True."""
    print("\n2. RUNNING CAPTURED COMMAND (should NOT see command output, but should see the captured content):")
    
    # Simple Python command with output capture
    result = subprocess.run(
        [sys.executable, "-c", "print('Captured command stdout output'); import sys; print('Captured command stderr output', file=sys.stderr)"],
        capture_output=True,
        text=True
    )
    
    print(f"Command exit code: {result.returncode}")
    print(f"Captured stdout: {result.stdout}")
    print(f"Captured stderr: {result.stderr}")
    print("Captured command completed\n")

def run_piped_command():
    """Run a command with explicit pipe configuration."""
    print("\n3. RUNNING COMMAND WITH EXPLICIT PIPES:")
    
    # Run with explicit pipe configuration
    process = subprocess.Popen(
        [sys.executable, "-c", "print('Piped command output'); import time; time.sleep(1); print('Delayed output')"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Read output incrementally
    print("Reading output as it arrives:")
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"  Received: {output.strip()}")
    
    # Get final results
    stdout, stderr = process.communicate()
    print(f"Final exit code: {process.returncode}")
    print(f"Remaining stdout: {stdout}")
    print(f"Stderr: {stderr}")
    print("Piped command completed\n")

def run_in_shell():
    """Run a command through the shell."""
    print("\n4. RUNNING COMMAND THROUGH SHELL:")
    
    # Command that uses shell features
    result = subprocess.run(
        "echo 'Shell command output' && python -c \"print('Python inside shell')\"",
        shell=True,
        capture_output=True,
        text=True
    )
    
    print(f"Command exit code: {result.returncode}")
    print(f"Captured stdout: {result.stdout}")
    print(f"Captured stderr: {result.stderr}")
    print("Shell command completed\n")

def run_main_script_sample():
    """Run a simulated version of your main.py with minimal functionality."""
    print("\n5. TESTING COMMAND SIMILAR TO WHAT YOUR TESTS ARE RUNNING:")
    
    # Create a simplified test script
    test_script = """
import sys
import time

# This simulates your src/main.py script
if __name__ == "__main__":
    print("Starting main.py simulation...")
    print(f"Arguments received: {sys.argv}")
    
    # Simulate processing
    print("Processing...")
    for i in range(3):
        print(f"Step {i+1}/3")
        time.sleep(0.5)
    
    print("Simulation completed successfully")
    """
    
    # Write to a temporary file
    with open("test_main_simulation.py", "w") as f:
        f.write(test_script)
    
    # Run it with command line arguments similar to your tests
    cmd = [sys.executable, "test_main_simulation.py", "--mode", "scrape", "--max-pages", "3"]
    print(f"Running command: {' '.join(cmd)}")
    
    # First run without capturing
    print("\nRUNNING WITHOUT CAPTURE:")
    subprocess.run(cmd)
    
    # Then run with capturing
    print("\nRUNNING WITH CAPTURE:")
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print(f"Command exit code: {result.returncode}")
    print(f"Captured stdout: {result.stdout}")
    print(f"Captured stderr: {result.stderr}")
    
    # Clean up
    import os
    os.remove("test_main_simulation.py")
    
    print("Main script simulation completed\n")

def main():
    """Run all subprocess tests."""
    print("=" * 50)
    print("SUBPROCESS TESTING SCRIPT")
    print("=" * 50)
    print("This script tests different ways of running and capturing subprocess output.")
    print("If you don't see any output from the commands themselves,")
    print("but you do see the 'Captured stdout/stderr' content,")
    print("it means the capture is working correctly.")
    
    # Run all tests
    run_direct_command()
    run_captured_command()
    run_piped_command()
    run_in_shell()
    run_main_script_sample()
    
    print("=" * 50)
    print("ALL SUBPROCESS TESTS COMPLETED")
    print("=" * 50)

if __name__ == "__main__":
    main() 