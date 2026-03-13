import sys
from pathlib import Path

import numpy as np
import rasterio
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

def normalize_band(band_data, optimize_highlights=False):
    """
    Normalizes 16-bit satellite imagery into an 8-bit format.
    If optimize_highlights is True, uses a wider percentile range and gamma 
    correction to preserve details in very bright areas.
    """
    # Exclude zero (often NoData) from the percentile calculation to avoid skewing
    valid_data = band_data[band_data > 0]
    if len(valid_data) == 0:
        return np.zeros_like(band_data, dtype=np.uint8)

    if optimize_highlights:
        # Retain more highlight data, but clip the absolute bottom 1% to reduce haze
        p_low, p_high = np.percentile(valid_data, (1, 99.9))
    else:
        # Standard linear stretch
        p_low, p_high = np.percentile(valid_data, (2, 98))
    
    # Clip extreme values
    band_clipped = np.clip(band_data, p_low, p_high)
    
    # Normalize to a 0.0 - 1.0 float scale first
    band_norm_float = (band_clipped - p_low) / (p_high - p_low)
    
    if optimize_highlights:
        # Apply gamma correction (gamma < 1 lifts midtones while preserving the newly saved highlights)
        gamma = 0.6
        band_norm_float = np.power(band_norm_float, gamma)
    
    # Scale to 8-bit (0-255)
    band_normalized = band_norm_float * 255.0
    
    return band_normalized.astype(np.uint8)

def main():
    console.print("\n[bold blue]🌍 Multispectral to RGB TIFF Converter[/bold blue]\n")

    # 1. Get input file
    while True:
        input_path = Prompt.ask("[bold yellow]Enter the path to your multispectral TIF file[/bold yellow]")
        if Path(input_path).exists() and Path(input_path).is_file():
            break
        console.print("[bold red]Error:[/bold red] File not found. Please try again.")

    # 2. Read metadata and prompt for bands
    try:
        with rasterio.open(input_path) as src:
            num_bands = src.count
            console.print(f"\n[green]Successfully opened image.[/green] Found [bold]{num_bands}[/bold] bands.")
            
            if num_bands < 3:
                console.print("[bold red]Error:[/bold red] Image must have at least 3 bands to create an RGB output.")
                sys.exit(1)

            # Rasterio uses 1-based indexing for bands
            r_band = IntPrompt.ask("Which band number is [bold red]Red[/bold red]?", default=3)
            g_band = IntPrompt.ask("Which band number is [bold green]Green[/bold green]?", default=2)
            b_band = IntPrompt.ask("Which band number is [bold blue]Blue[/bold blue]?", default=1)

            # 3. Prompt for Highlight Optimization
            console.print("\n[cyan]Highlight Optimization preserves detail in bright areas like clouds, snow, or bright roofs by applying a non-linear gamma stretch.[/cyan]")
            opt_highlights = Confirm.ask("Enable Highlight Optimization?", default=True)

            # 4. Get output file
            output_path = Prompt.ask("\n[bold yellow]Enter the path for the output RGB TIF file[/bold yellow]", default="output_rgb.tif")

            # 5. Processing with Progress Bar
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
                
                # Create a task for reading and normalizing each band, plus one for writing
                task_total = progress.add_task("[cyan]Processing Image...", total=4)

                # Read and normalize bands
                progress.update(task_total, description=f"[red]Reading & Normalizing Red Band ({r_band})...[/red]")
                r_data = normalize_band(src.read(r_band), optimize_highlights=opt_highlights)
                progress.advance(task_total)

                progress.update(task_total, description=f"[green]Reading & Normalizing Green Band ({g_band})...[/green]")
                g_data = normalize_band(src.read(g_band), optimize_highlights=opt_highlights)
                progress.advance(task_total)

                progress.update(task_total, description=f"[blue]Reading & Normalizing Blue Band ({b_band})...[/blue]")
                b_data = normalize_band(src.read(b_band), optimize_highlights=opt_highlights)
                progress.advance(task_total)

                # Write out
                progress.update(task_total, description="[magenta]Saving RGB image...[/magenta]")
                with rasterio.open(output_path, 'w', **profile) as dst:
                    dst.write(r_data, 1)
                    dst.write(g_data, 2)
                    dst.write(b_data, 3)
                progress.advance(task_total)

            console.print(f"\n[bold green]✅ Success![/bold green] RGB image saved to: [bold]{output_path}[/bold]\n")

    except Exception as e:
        console.print(f"\n[bold red]An error occurred during processing:[/bold red] {e}")

if __name__ == "__main__":
    main()