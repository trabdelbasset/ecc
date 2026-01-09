import sys
import json
import argparse
import os

# Add project root to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "../../.."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from chipcompiler.data.workspace import create_workspace, PDK
from chipcompiler.data.parameter import Parameters

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', choices=['init', 'load'], required=True)
    parser.add_argument('--path', required=True)
    parser.add_argument('--name', default='Untitled_Project')
    parser.add_argument('--from-gui', action='store_true')
    
    args, unknown = parser.parse_known_args()

    try:
        if args.action == 'init':
            # Initialize a new workspace
            ws = create_workspace(
                directory=args.path,
                origin_def="",
                origin_verilog="",
                pdk=PDK(name="Default_PDK"),
                parameters=Parameters(data={"Design": args.name, "Top module": "top"})
            )
            result = {
                "status": "success",
                "message": f"Project initialized at {args.path}",
                "project": {
                    "name": args.name,
                    "path": args.path
                }
            }
        
        elif args.action == 'load':
            # Load existing workspace state
            flow_path = os.path.join(args.path, "flow.json")
            if not os.path.exists(flow_path):
                raise Exception("Not a valid ECC project directory (flow.json missing)")
            
            with open(flow_path, 'r') as f:
                flow_data = json.load(f)
            
            # Extract project name from parameters.json if it exists
            project_name = os.path.basename(args.path)
            param_path = os.path.join(args.path, "parameters.json")
            if os.path.exists(param_path):
                with open(param_path, 'r') as f:
                    params = json.load(f)
                    project_name = params.get("Design", project_name)

            result = {
                "status": "success",
                "project": {
                    "name": project_name,
                    "path": args.path,
                    "flow": flow_data
                }
            }

        print(json.dumps(result))

    except Exception as e:
        print(json.dumps({
            "status": "error",
            "message": str(e)
        }))

if __name__ == "__main__":
    main()
