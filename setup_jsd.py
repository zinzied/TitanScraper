import os
import sys
import subprocess
import json
import shutil

GO_WRAPPER_SOURCE = r"""
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"

	"github.com/fxnatic/jsd-solver-go/solver"
)

type Input struct {
	Mode      string            `json:"mode"` // "auto" or "manual"
	URL       string            `json:"url"`
	R         string            `json:"r"`
	T         string            `json:"t"`
	ScriptURL string            `json:"script_url"`
	Cookies   map[string]string `json:"cookies"`
}

type Output struct {
	Success     bool   `json:"success"`
	CfClearance string `json:"cf_clearance"`
	StatusCode  int    `json:"status_code"`
	Error       string `json:"error,omitempty"`
}

func main() {
	// Disable standard logger to avoid polluting stdout (which we use for JSON)
	log.SetOutput(os.Stderr)

	var input Input
	if err := json.NewDecoder(os.Stdin).Decode(&input); err != nil {
		printOutput(Output{Success: false, Error: "Failed to decode input JSON: " + err.Error()})
		return
	}

	var res *solver.Result
	var err error

	if input.Mode == "manual" {
		// Manual mode: R, T supplied
		data := solver.SolveData{
			R:         input.R,
			T:         input.T,
			ScriptURL: input.ScriptURL,
			Cookies:   input.Cookies,
		}
		
		# We need to construct a solver first to call SolveFromData? 
		# Looking at README: s, err := solver.NewSolver(...) then s.SolveFromData(data)
		# Actually README says:
		# s, err := solver.NewSolver("https://www.example.com", false)
		# res, err = s.SolveFromData(data)
		
		s, err := solver.NewSolver(input.URL, false)
		if err != nil {
			printOutput(Output{Success: false, Error: "Failed to init solver: " + err.Error()})
			return
		}
		res, err = s.SolveFromData(data)

	} else {
		// Auto mode: Fetch homepage first
		s, err := solver.NewSolver(input.URL, false)
		if err != nil {
			printOutput(Output{Success: false, Error: "Failed to init solver: " + err.Error()})
			return
		}
		res, err = s.Solve()
	}

	if err != nil {
		printOutput(Output{Success: false, Error: "Solver failed: " + err.Error()})
		return
	}

	printOutput(Output{
		Success:     res.Success,
		CfClearance: res.CfClearance,
		StatusCode:  res.StatusCode,
	})
}

func printOutput(out Output) {
	enc := json.NewEncoder(os.Stdout)
	enc.Encode(out)
}
"""

def check_go_installed():
    try:
        subprocess.run(["go", "version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def setup_jsd_solver():
    print("[-] Setting up JSD Solver...")
    
    if not check_go_installed():
        print("[!] Go is not installed or not in PATH.")
        print("    Please install Go from https://go.dev/dl/ and try again.")
        print("    After installing, restart your terminal.")
        return False

    base_dir = os.path.dirname(os.path.abspath(__file__))
    solver_dir = os.path.join(base_dir, "titan", "solver_go")
    
    if os.path.exists(solver_dir):
        # Clean up existing to ensure fresh build
        # shutil.rmtree(solver_dir)
        pass # Keep it if exists? Better to rebuild.
        
    if not os.path.exists(solver_dir):
        os.makedirs(solver_dir)

    # Write main.go
    main_go_path = os.path.join(solver_dir, "main.go")
    with open(main_go_path, "w") as f:
        f.write(GO_WRAPPER_SOURCE)
    
    print(f"[-] Created Go wrapper at {main_go_path}")

    # Initialize module
    try:
        subprocess.run(["go", "mod", "init", "jsd-wrapper"], cwd=solver_dir, check=True, capture_output=True)
    except subprocess.CalledProcessError:
        # likely already initialized
        pass

    # Get dependency
    print("[-] Fetching dependencies (github.com/fxnatic/jsd-solver-go)...")
    try:
        subprocess.run(["go", "get", "github.com/fxnatic/jsd-solver-go"], cwd=solver_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Failed to fetch dependencies: {e}")
        return False

    # Build
    print("[-] Building binary...")
    output_bin = "jsd_solver.exe" if os.name == 'nt' else "jsd_solver"
    try:
        subprocess.run(["go", "build", "-o", output_bin], cwd=solver_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Build failed: {e}")
        return False

    bin_path = os.path.join(solver_dir, output_bin)
    if os.path.exists(bin_path):
        print(f"[+] Successfully built JSD Solver binary: {bin_path}")
        return True
    else:
        print("[!] Build command succeeded but binary not found.")
        return False

if __name__ == "__main__":
    setup_jsd_solver()
