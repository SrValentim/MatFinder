# MatFinder

MatFinder is a powerful tool for materials scientists, designed to streamline the process of materials research by integrating multiple databases and providing advanced analysis tools. It combines data from various sources, including OQMD and Material Project, into a single, user-friendly interface.

## Key Features

- **Unified Database:** Access data from multiple materials science databases in one place.
- **PhaseDRX:** An advanced tool for analyzing diffractograms, fully integrated with the materials databases to accelerate phase identification.
- **CIF Manipulation:** Manipulate CIF files, including adjusting volume and lattice parameters, to achieve a better theoretical-experimental fit in Rietveld refinement.

## Installation

To install and run MatFinder, follow these steps:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/matfinder.git
   cd matfinder
   ```

2. **Install the dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

To start the application, run the following command in the project's root directory:

```bash
python run_matfinder.py
```

This will launch the MatFinder graphical user interface, where you can access all the features and tools.

## Project Structure

The project is organized as follows:

- `run_matfinder.py`: The main script to run the application.
- `setup.py`: The setup script for creating executables.
- `requirements.txt`: A list of the project's dependencies.
- `matfinder/`: The main application package.
  - `assets/`: Contains all the application's assets, such as icons and logos.
  - `core/`: Contains the core logic of the application.
  - `data/`: Contains the application's data files.
  - `tools/`: Contains the application's tools, such as PhaseDRX.
  - `app_main.py`: The main application window.
- `docs/`: Contains the project's documentation.
- `scripts/`: Contains additional scripts for the project.
- `tests/`: Contains the project's tests.

## License

MatFinder is published under the **GNU General Public License v3.0 (GPLv3)**.

### Key terms
- You may use, study, modify, and redistribute the software freely.
- Any distribution (modified or not) **must** remain under GPLv3 and include the source code or a written offer to obtain it.
- There is **no warranty**; use at your own risk.

### Attribution
Developed by **Raynner Valentim (Universidade Federal do Amazonas - UFAM)**. For donations, research collaborations, or enterprise support agreements, please contact <Raynnervalentim@hotmail.com>.

The full license text is available in the [`LICENSE`](LICENSE) file.
