import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import median_filter
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeElapsedColumn
)

console = Console()

def normalize_sar_band(band_data):
    """
    Applies a 2nd-98th percentile stretch for SAR data.
    """
    valid_data = band_data[band_data > 0]
    if len(valid_data) == 0:
        return np.zeros_like(band_data, dtype=np.uint8)

    p2, p98 = np.percentile(valid_data, (2, 98))
    
    band_clipped = np.clip(band_data, p2, p98)
    
    if p98 == p2:
        return np.zeros_like(band_data, dtype=np.uint8)
        
    band_normalized = (band_clipped - p2) / (p98 - p2) * 255.0
    
    return band_normalized.astype(np.uint8)

def apply_speckle_filter(band_data, size=3):
    """
    Applies a median filter to reduce SAR speckle noise.
    """
    return median_filter(band_data, size=size)

def main():
    console.print("\n[bold magenta]📡 SAR to RGB TIFF Converter (with Speckle Filter)[/bold magenta]\n")

    # 1. Get input file
    while True:
        input_path = Prompt.ask("[bold yellow]Enter the path to your SAR TIF file[/bold yellow]")
        if Path(input_path).exists() and Path(input_path).is_file():
            break
        console.print("[bold red]Error:[/bold red] File not found. Please try again.")

    # 2. Read metadata and configure options
    try:
        with rasterio.open(input_path) as src:
            num_bands = src.count
            console.print(f"\n[green]Successfully opened image.[/green] Found [bold]{num_bands}[/bold] bands.")
            
            if num_bands < 2:
                console.print("[bold red]Error:[/bold red] This script requires at least 2 bands (e.g., VV and VH) to create a ratio composite.")
                sys.exit(1)

            # Band selection
            band_a_idx = IntPrompt.ask("Which band number is your primary polarization (e.g., VV)?", default=1)
            band_b_idx = IntPrompt.ask("Which band number is your secondary polarization (e.g., VH)?", default=2)

            # Optional speckle filter
            console.print("\n[italic]SAR images naturally contain grainy speckle noise. A median filter can smooth this out.[/italic]")
            use_filter = Confirm.ask("Would you like to apply a speckle filter?", default=True)
            filter_size = 3
            if use_filter:
                filter_size = IntPrompt.ask("Enter filter window size (e.g., 3 for 3x3, 5 for 5x5). Higher = smoother but blurrier", default=3)

            # Output path
            output_path = Prompt.ask("\n[bold yellow]Enter the path for the output RGB TIF file[/bold yellow]", default="output_sar_rgb.tif")

            profile = src.profile
            profile.update(
                count=3,
                dtype=rasterio.uint8,
                photometric='RGB'
            )

            console.print("\n")
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TaskProgressColumn(),
                TimeElapsedColumn(),
                console=console
            ) as progress:
                
                task_total = progress.add_task("[cyan]Processing SAR Image...", total=4)

                # Helper string for progress bar
                action_text = "Filtering & Normalizing" if use_filter else "Normalizing"

                # Read, (Filter), and Normalize Band 1 (Red)
                progress.update(task_total, description=f"[red]Reading, {action_text} Primary Band ({band_a_idx}) for Red...[/red]")
                raw_band_a = src.read(band_a_idx).astype(np.float32)
                if use_filter:
                    raw_band_a = apply_speckle_filter(raw_band_a, size=filter_size)
                r_data = normalize_sar_band(raw_band_a)
                progress.advance(task_total)

                # Read, (Filter), and Normalize Band 2 (Green)
                progress.update(task_total, description=f"[green]Reading, {action_text} Secondary Band ({band_b_idx}) for Green...[/green]")
                raw_band_b = src.read(band_b_idx).astype(np.float32)
                if use_filter:
                    raw_band_b = apply_speckle_filter(raw_band_b, size=filter_size)
                g_data = normalize_sar_band(raw_band_b)
                progress.advance(task_total)

                # Calculate Ratio (Blue)
                progress.update(task_total, description="[blue]Calculating Primary/Secondary Ratio for Blue...[/blue]")
                raw_ratio = np.divide(raw_band_a, raw_band_b, out=np.zeros_like(raw_band_a), where=(raw_band_b != 0))
                b_data = normalize_sar_band(raw_ratio)
                progress.advance(task_total)

                # Write out
                progress.update(task_total, description="[magenta]Saving SAR RGB image...[/magenta]")
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(r_data, 1)
                    dst.write(g_data, 2)
                    dst.write(b_data, 3)
                progress.advance(task_total)

            console.print(f"\n[bold green]✅ Success![/bold green] SAR RGB image saved to: [bold]{output_path}[/bold]\n")

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during processing:[/bold red] {e}")

if __name__ == "__main__":
    main()