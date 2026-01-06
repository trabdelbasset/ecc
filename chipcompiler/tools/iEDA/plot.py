#!/usr/bin/env python
# -*- encoding: utf-8 -*-
import os
import pandas as pd
import matplotlib.pyplot as plt
from chipcompiler.data import WorkspaceStep, Workspace, Parameters, StepEnum
from chipcompiler.utility import json_read

class IEDAPlot:
    def __init__(self, workspace: Workspace, step: WorkspaceStep):
        self.workspace = workspace
        self.step = step
    
    def plot(self) -> bool:
        match self.step.name:
            case StepEnum.PLACEMENT.value | StepEnum.CTS.value:
                json_map_path = self.step.feature.get("map", "")
                json_map = json_read(json_map_path)
                if not json_map:
                    return False
                
                # density map
                self.plot_array_map(input_path=json_map.get("Density", {}).get("cell", {}).get("allcell_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("cell", {}).get("macro_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("cell", {}).get("stdcell_density", ""))
                
                self.plot_array_map(input_path=json_map.get("Density", {}).get("margin", {}).get("horizontal", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("margin", {}).get("union", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("margin", {}).get("vertical", ""))
                
                self.plot_array_map(input_path=json_map.get("Density", {}).get("net", {}).get("allnet_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("net", {}).get("global_net_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("net", {}).get("local_net_density", ""))
                
                self.plot_array_map(input_path=json_map.get("Density", {}).get("pin", {}).get("allcell_pin_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("pin", {}).get("macro_pin_density", ""))
                self.plot_array_map(input_path=json_map.get("Density", {}).get("pin", {}).get("stdcell_pin_density", ""))
                
                # congenstion
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("horizontal", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("union", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("egr", {}).get("vertical", ""))
                
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("horizontal", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("union", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("lutrudy", {}).get("vertical", ""))
                
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("horizontal", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("union", ""))
                self.plot_array_map(input_path=json_map.get("Congestion", {}).get("map", {}).get("rudy", {}).get("vertical", ""))
                
            case default:
                self.workspace.logger.warning(f"Step {self.step.name} not supported for plotting.")
        
        self.workspace.logger.info(f"Plotting completed for step {self.step.name}")
        return True
        
    def plot_array_map(self, input_path : str, output_path : str=None) -> bool:
        """
        Plot array map from CSV file.
        
        Args:
            input_path (str): Path to the input CSV file.
            output_path (str, optional): Path to the output PNG file. Defaults to None.
        
        Returns:
            bool: True if the plot is successful, False otherwise.
        """
        if not os.path.exists(input_path) or not input_path.lower().endswith(".csv"):
            return False
        
        if not output_path:
            output_path = input_path.replace(".csv", ".png")
        
        try:
            # Read CSV data
            df = pd.read_csv(input_path)
            
            # Create a figure and axis
            plt.figure(figsize=(10, 8))
            
            # Assuming the CSV has columns that can be used as x, y, and value
            # If the CSV has a grid structure without headers, we can use it directly
            if df.shape[1] > 1:
                # Try different approaches based on CSV structure
                if 'x' in df.columns and 'y' in df.columns and 'value' in df.columns:
                    # For CSV with x, y, value columns (scatter plot with color)
                    plt.scatter(df['x'], df['y'], c=df['value'], cmap='viridis')
                    plt.colorbar(label='Value')
                else:
                    # For matrix-like CSV data (heatmap)
                    plt.imshow(df.values, cmap='viridis', origin='lower')
                    plt.colorbar(label='Value')
                    plt.xticks(range(df.shape[1]), df.columns if df.columns[0] != '0' else range(df.shape[1]))
                    plt.yticks(range(df.shape[0]))
            else:
                # For 1D data
                plt.plot(df.values)
            
            title, _ = os.path.splitext(os.path.basename(input_path))
            plt.title(title)
            plt.xlabel('X')
            plt.ylabel('Y')
            
            # Save the plot
            plt.savefig(output_path, dpi=300, bbox_inches='tight')
            plt.close()
            
            self.workspace.logger.info(f"Plot image saved to {output_path}")
            
            return True
        except Exception as e:
            self.workspace.logger.error(f"Error plotting array map: {e}")
            return False
    