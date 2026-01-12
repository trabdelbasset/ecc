#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os

import concurrent.futures
from tqdm import tqdm
from chipcompiler.data import WorkspaceStep, Workspace, Parameters, StepEnum
from chipcompiler.utility import json_read
from chipcompiler.utility.plot import plot_csv_map

class IEDAPlot:
    def __init__(self, workspace: Workspace, step: WorkspaceStep):
        self.workspace = workspace
        self.step = step
    
    def plot(self) -> bool:
        match self.step.name:
            case StepEnum.PLACEMENT.value | StepEnum.CTS.value:
                return self.plot_placement_heatmap()
            case StepEnum.ROUTING.value:
                return self.plot_routing_heatmap()
                
            case default:
                self.workspace.logger.warning(f"Step {self.step.name} not supported for plotting.")
        
        self.workspace.logger.info(f"Plotting completed for step {self.step.name}")
        return True
    
    def plot_placement_heatmap(self):
        json_map_path = self.step.feature.get("map", "")
        json_map = json_read(json_map_path)
        if not json_map:
            return False
        
        # density map
        csv_list = []
        csv_list.extend([
            json_map.get("Density", {}).get("cell", {}).get("allcell_density", ""),
            json_map.get("Density", {}).get("cell", {}).get("macro_density", ""),
            json_map.get("Density", {}).get("cell", {}).get("stdcell_density", ""),
            json_map.get("Density", {}).get("margin", {}).get("horizontal", ""),
            json_map.get("Density", {}).get("margin", {}).get("union", ""),
            json_map.get("Density", {}).get("margin", {}).get("vertical", ""),
            json_map.get("Density", {}).get("net", {}).get("allnet_density", ""),
            json_map.get("Density", {}).get("net", {}).get("global_net_density", ""),
            json_map.get("Density", {}).get("net", {}).get("local_net_density", ""),
            json_map.get("Density", {}).get("pin", {}).get("allcell_pin_density", ""),
            json_map.get("Density", {}).get("pin", {}).get("macro_pin_density", ""),
            json_map.get("Density", {}).get("pin", {}).get("stdcell_pin_density", ""),
            json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("horizontal", ""),
            json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("union", ""),
            json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("vertical", ""),
            json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("horizontal", ""),
            json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("union", ""),
            json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("vertical", ""),
            json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("horizontal", ""),
            json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("union", ""),
            json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("vertical", "")
        ])
        self.plot_array_maps(input_paths=csv_list)
        
        return True
    
    def plot_routing_heatmap(self) -> bool:
        data_dir = self.step.data.get(f"{StepEnum.ROUTING.value}", "")
        if not os.path.exists(data_dir):
            return False
        
        csv_list = []
        for root, dirs, files in os.walk(data_dir):
            for file in files:
                if file.endswith(".csv"):
                    csv_path = os.path.join(root, file)
                    csv_list.append(csv_path)
        
        self.plot_array_maps(input_paths=csv_list)
                    
        return True
    
    def plot_array_maps(self, input_paths : list[str]):
        """
        Plot array maps from multiple CSV files using multi-threading with progress bar.
        
        Args:
            input_paths (list[str]): List of paths to input CSV files.
        """
        if not input_paths:
            return
        
        # Filter out invalid paths
        valid_paths = [path for path in input_paths if path and os.path.exists(path) and path.lower().endswith(".csv")]
        
        if not valid_paths:
            self.workspace.logger.warning("No valid CSV files found for plotting.")
            return
        
        self.workspace.logger.info(f"Plotting {len(valid_paths)} array maps with multi-threading...")
        
        # Use ThreadPoolExecutor for multi-threading with progress bar (limit to 10 threads)
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Create a progress bar
            results = list(tqdm(
                executor.map(plot_csv_map, valid_paths),
                total=len(valid_paths),
                desc="Plotting array maps",
                unit="file"
            ))
        
        # Count successful and failed plots
        successful = sum(results)
        failed = len(results) - successful
        
        self.workspace.logger.info(f"Plotting completed: {successful} successful, {failed} failed.")
