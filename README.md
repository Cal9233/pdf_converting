# 🏦 PDF to Excel Converter

A professional Python application that converts PDF credit card statements to Excel format with comprehensive validation and reporting.

## ✨ Features

- **Multi-Bank Support**: American Express and Chase statements
- **Smart Parsing**: Automatic cardholder name detection and transaction extraction
- **Validation Engine**: Comprehensive accuracy checking with confidence scoring
- **Excel Export**: Clean, formatted Excel files with proper column ordering
- **Progress Tracking**: Real-time GUI progress window
- **Validation Reports**: Detailed accuracy reports for quality assurance
- **Configurable**: Easy customization through configuration files

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- PDF statements from supported banks (AmEx, Chase)

### Installation

1. **Clone or download the project**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Place PDF statements** in the `Convert/` folder
2. **Run the application:**
   ```bash
   python src/main.py
   ```
3. **Check results** in the `Excel/` folder

## 📁 Project Structure

```
pdf_to_excel_converter/
├── src/                     # Main source code
│   ├── main.py             # Application entry point
│   ├── core/               # Core converter logic
│   ├── parsers/            # Bank-specific PDF parsers
│   ├── validators/         # Transaction validation
│   ├── exporters/          # Excel file creation
│   ├── ui/                 # User interface components
│   └── utils/              # Utility functions
├── config/                 # Configuration settings
├── Convert/                # Input folder (place PDFs here)
├── Excel/                  # Output folder (Excel files created here)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## 🔧 Configuration

Customize the application by editing `config/settings.py`:

- **Folder names**: Change default input/output folders
- **Validation thresholds**: Adjust confidence scoring
- **Excel formatting**: Modify column order and styling
- **UI settings**: Customize window dimensions and timing

## 📊 Supported Banks

### American Express

- Business and personal statements
- Automatic cardholder detection
- Transaction validation

### Chase

- Credit card statements
- Date range detection
- Multi-cardholder support

## 🎯 Output

### Excel Files

- `AmEx_Combined_YYYYMMDD_HHMMSS.xlsx`
- `Chase_Combined_YYYYMMDD_HHMMSS.xlsx`

### Validation Reports

- `Validation_Report_YYYYMMDD_HHMMSS.txt`
- Confidence scores and accuracy metrics
- Potential missed transactions

## 📈 Validation Features

- **Confidence Scoring**: 0-100% accuracy rating
- **Transaction Counting**: Estimates vs. extracted comparison
- **Amount Validation**: Cross-checks with statement totals
- **Missed Detection**: Identifies potentially missed transactions

## 🛠️ Development

### Architecture

The application follows a modular architecture with clear separation of concerns:

- **Core**: Main orchestration and folder management
- **Parsers**: Bank-specific PDF processing logic
- **Validators**: Transaction accuracy and name validation
- **Exporters**: Excel file creation and report generation
- **UI**: Progress windows and user interaction
- **Utils**: Shared utility functions

### Adding New Banks

1. Create new parser in `src/parsers/`
2. Add bank keywords to `config/settings.py`
3. Update detection logic in `converter.py`

## 📋 Requirements

- **Python 3.7+**
- **pandas**: Data manipulation and Excel export
- **openpyxl**: Excel file creation and formatting
- **pdfplumber**: PDF text extraction
- **tkinter**: GUI components (included with Python)

## 🐛 Troubleshooting

### Common Issues

1. **"No module named 'config'"**

   - Ensure you're running from the project root directory
   - Try: `python -m src.main`

2. **"No PDF files found"**

   - Check that PDFs are in the `Convert/` folder
   - Ensure files have `.pdf` extension

3. **GUI not working**
   - The application will fall back to console mode
   - Check tkinter installation: `python -m tkinter`

### Getting Help

1. Check the validation report for processing details
2. Review console output for error messages
3. Ensure PDF files are valid and not password-protected

## 📝 License

This project is for educational and personal use.

## 🏆 Acknowledgments

Built with modern Python best practices:

- Modular architecture
- Configuration management
- Comprehensive validation
- Professional documentation
