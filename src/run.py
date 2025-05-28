import subprocess
import os
import sys
import time
from pathlib import Path
import signal
import shutil
import locale
import io

# Set console output encoding to UTF-8
if os.name == 'nt':  # For Windows
    # Try to set console mode to support UTF-8
    os.system('chcp 65001 > NUL')
    # Set environment variables to enforce UTF-8
    os.environ['PYTHONIOENCODING'] = 'utf-8'

# Get the directory of the current script
CURRENT_DIR = Path(__file__).parent.absolute()
PROJECT_ROOT = CURRENT_DIR.parent  # Go up one level from src folder
BACKEND_DIR = CURRENT_DIR / "backend"
FRONTEND_DIR = CURRENT_DIR / "frontend"

# Store processes to be able to terminate them properly
processes = []

def find_executable(name):
    """Find executable in PATH or common installation directories"""
    # Check if it's in PATH
    executable = shutil.which(name)
    if executable:
        return executable
        
    # Common locations for npm on Windows
    if name == "npm" and os.name == "nt":
        common_paths = [
            r"C:\Program Files\nodejs\npm.cmd",
            r"C:\Program Files (x86)\nodejs\npm.cmd",
            os.path.expanduser(r"~\AppData\Roaming\npm\npm.cmd"),
            # Add Node.js installation from NVM for Windows
            os.path.expanduser(r"~\AppData\Roaming\nvm\current\npm.cmd")
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
                
    return None

def run_backend():
    """Run the FastAPI backend"""
    print("Starting backend server...")
    
    # Check if the main.py exists
    if not (BACKEND_DIR / "main.py").exists():
        print(f"Backend main.py not found at {BACKEND_DIR / 'main.py'}")
        print(f"Files in backend directory: {os.listdir(BACKEND_DIR)}")
        raise FileNotFoundError("Backend main.py not found")
    
    # Set environment variables for backend process
    backend_env = os.environ.copy()
    backend_env['PYTHONIOENCODING'] = 'utf-8'
    backend_env['PYTHONUTF8'] = '1'
    
    # Find uvicorn executable
    uvicorn_executable = find_executable("uvicorn")
    if not uvicorn_executable:
        # If uvicorn is not in PATH, use python -m uvicorn
        backend_cmd = [sys.executable, "-m", "uvicorn", "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    else:
        # Use direct uvicorn command
        backend_cmd = [uvicorn_executable, "main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"]
    
    print(f"Running command: {' '.join(backend_cmd)}")
    backend_process = subprocess.Popen(
        backend_cmd,
        cwd=BACKEND_DIR,  # Run from backend directory so main:app resolves correctly
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=False,  # Changed to False to handle binary output directly
        bufsize=1,
        env=backend_env
    )
    processes.append(backend_process)
    return backend_process

def run_frontend():
    """Run the frontend development server"""
    print("Starting frontend server...")
    
    # Check if package.json exists in the frontend directory
    if not (FRONTEND_DIR / "package.json").exists():
        print(f"Frontend package.json not found at {FRONTEND_DIR / 'package.json'}")
        print(f"Files in frontend directory: {os.listdir(FRONTEND_DIR)}")
        raise FileNotFoundError("Frontend package.json not found")
    
    # Try to find npm executable
    npm_executable = find_executable("npm")
    if not npm_executable:
        print("npm command not found in PATH or common locations.")
        print("Please ensure Node.js and npm are installed and in your PATH.")
        print("\nAlternatives:")
        print("1. Open a new terminal and run 'cd src/frontend && npm run dev' manually")
        print("2. Install Node.js from https://nodejs.org/")
        raise FileNotFoundError("npm executable not found")
    
    print(f"Found npm at: {npm_executable}")
    
    # Set environment variables for frontend process
    frontend_env = os.environ.copy()
    
    # Use npm run dev for frontend
    frontend_cmd = [npm_executable, "run", "dev"]
    
    print(f"Running command: {' '.join(frontend_cmd)}")
    try:
        frontend_process = subprocess.Popen(
            frontend_cmd,
            cwd=FRONTEND_DIR,  # Run from frontend directory
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=False,  # Changed to False to handle binary output directly
            bufsize=1,
            env=frontend_env
        )
        processes.append(frontend_process)
        return frontend_process
    except FileNotFoundError as e:
        print(f"Error running npm: {e}")
        print("Environment PATH:", os.environ.get("PATH", ""))
        raise

def stream_output(process, prefix):
    """Stream the output of a process with a prefix, handling binary data properly"""
    while True:
        # Read output as binary data
        output = process.stdout.readline()
        if not output:
            # Process has ended or pipe is closed
            break
            
        # Try different encodings, starting with utf-8
        try:
            line = output.decode('utf-8').rstrip()
            print(f"{prefix}: {line}", flush=True)
        except UnicodeDecodeError:
            try:
                # Try with latin-1 as a fallback (will always decode)
                line = output.decode('latin-1').rstrip()
                print(f"{prefix}: {line}", flush=True)
            except Exception:
                # Last resort - just output something
                print(f"{prefix}: [Non-decodable output]", flush=True)

def handle_exit(signum, frame):
    """Handle exit signals gracefully"""
    print("\nShutting down servers...")
    for process in processes:
        process.terminate()
    sys.exit(0)

def main():
    # Print system encoding information
    print(f"Default encoding: {sys.getdefaultencoding()}")
    print(f"Filesystem encoding: {sys.getfilesystemencoding()}")
    print(f"Locale: {locale.getpreferredencoding()}")
    
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, handle_exit)
    signal.signal(signal.SIGTERM, handle_exit)
    
    try:
        print(f"Project root: {PROJECT_ROOT}")
        print(f"Backend directory: {BACKEND_DIR}")
        print(f"Frontend directory: {FRONTEND_DIR}")
        
        # Start backend
        backend_process = run_backend()
        
        # Wait a bit for backend to start
        time.sleep(2)
        
        try:
            # Start frontend
            frontend_process = run_frontend()
            
            # Stream outputs
            import threading
            backend_thread = threading.Thread(target=stream_output, args=(backend_process, "BACKEND"))
            
            if frontend_process:
                frontend_thread = threading.Thread(target=stream_output, args=(frontend_process, "FRONTEND"))
                frontend_thread.daemon = True
                frontend_thread.start()
            
            backend_thread.daemon = True
            backend_thread.start()
            
            # Keep the main thread alive
            while True:
                if backend_process.poll() is not None:
                    print("Backend server stopped unexpectedly.")
                    break
                if frontend_process and frontend_process.poll() is not None:
                    print("Frontend server stopped unexpectedly.")
                    break
                time.sleep(1)
        except FileNotFoundError as e:
            print(f"Could not start frontend: {e}")
            print("Running backend only. Please start frontend manually in another terminal.")
            # Keep the main thread alive for backend only
            while True:
                if backend_process.poll() is not None:
                    print("Backend server stopped unexpectedly.")
                    break
                time.sleep(1)
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Clean up on exit
        for process in processes:
            if process.poll() is None:  # If process is still running
                process.terminate()

if __name__ == "__main__":
    main()
