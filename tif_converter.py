import os
import sys
from pathlib import Path
from PIL import Image
from rich.console import Console
from rich.prompt import Prompt, IntPrompt, Confirm
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

console = Console()

def process_image(file_path, output_dir, target_format, scale_ratio):
    try:
        with Image.open(file_path) as img:
            # Calculate new dimensions
            new_width = max(1, int(img.width * scale_ratio))
            new_height = max(1, int(img.height * scale_ratio))
            
            # Resize image using high-quality downsampling
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Convert color mode if necessary (e.g., RGBA/CMYK to RGB for JPG)
            if target_format == "jpg" and resized_img.mode != "RGB":
                resized_img = resized_img.convert("RGB")
                
            # Construct output file path
            output_filename = f"{file_path.stem}.{target_format}"
            output_path = output_dir / output_filename
            
            # Save the image
            # Optimizing for WebP and JPG to help reduce size further
            if target_format in ["jpg", "webp"]:
                resized_img.save(output_path, quality=85, optimize=True)
            else:
                resized_img.save(output_path, optimize=True)
                
            return True, None
    except Exception as e:
        return False, str(e)

def main():
    console.print("[bold cyan]📸 Interactive TIF/TIFF Image Converter[/bold cyan]", justify="center")
    console.print("This script will convert your TIF files, scale them down, and save them in a new folder.\n")

    # 1. Get Source Directory
    while True:
        src_input = Prompt.ask("[bold yellow]Enter the folder path containing your TIF/TIFF images[/bold yellow]")
        src_dir = Path(src_input.strip('\'"')) # Strip accidental quotes
        
        if src_dir.is_dir():
            break
        console.print(f"[bold red]Error:[/bold red] The directory '{src_dir}' does not exist. Please try again.")

    # Find TIF files
    tif_files = [f for f in src_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.tif', '.tiff']]
    
    if not tif_files:
        console.print("[bold red]No TIF or TIFF files found in the specified directory. Exiting.[/bold red]")
        sys.exit(0)
        
    console.print(f"[bold green]Found {len(tif_files)} TIF/TIFF files![/bold green]\n")

    # 2. Get Target Format
    format_choices = ["jpg", "png", "webp"]
    target_format = Prompt.ask(
        "[bold yellow]Select output format[/bold yellow]", 
        choices=format_choices, 
        default="jpg"
    )

    # 3. Get Scale Ratio
    scale_percent = IntPrompt.ask(
        "[bold yellow]Enter output size percentage (1-100)[/bold yellow]\n[dim](e.g., 50 will resize images to 50% of their original width and height)[/dim]", 
        default=50
    )
    
    # Validate percentage
    scale_percent = max(1, min(100, scale_percent))
    scale_ratio = scale_percent / 100.0

    # 4. Confirm and setup output directory
    output_dir = src_dir / f"converted_{target_format}_{scale_percent}pct"
    
    console.print("\n[bold cyan]--- Summary ---[/bold cyan]")
    console.print(f"Files to process: [bold]{len(tif_files)}[/bold]")
    console.print(f"Output format:    [bold]{target_format.upper()}[/bold]")
    console.print(f"Scale ratio:      [bold]{scale_percent}%[/bold]")
    console.print(f"Output folder:    [bold]{output_dir}[/bold]")
    
    if not Confirm.ask("\nProceed with conversion?"):
        console.print("[bold red]Operation cancelled by user.[/bold red]")
        sys.exit(0)

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # 5. Process files with a Progress Bar
    successful = 0
    failed = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task("[cyan]Converting images...", total=len(tif_files))
        
        for file_path in tif_files:
            progress.update(task, description=f"[cyan]Converting {file_path.name}...")
            
            success, error_msg = process_image(file_path, output_dir, target_format, scale_ratio)
            
            if success:
                successful += 1
            else:
                failed += 1
                progress.console.print(f"[red]Failed to convert {file_path.name}: {error_msg}[/red]")
                
            progress.advance(task)

    # Final Output
    console.print("\n[bold green]🎉 Conversion Complete![/bold green]")
    console.print(f"Successfully converted: [bold green]{successful}[/bold green]")
    if failed > 0:
        console.print(f"Failed to convert: [bold red]{failed}[/bold red]")

if __name__ == "__main__":
    main()