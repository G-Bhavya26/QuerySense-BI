from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def create_pdf_report(dataframe: pd.DataFrame, insights: str, output_path: str = "report.pdf") -> str:
    """
    Generates a premium PDF report containing data insights and a formatted data table.
    """
    try:
        # Use landscape to fit more columns
        doc = SimpleDocTemplate(output_path, pagesize=landscape(letter),
                                rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=18)
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom Styles
        title_style = ParagraphStyle(
            name="ReportTitle",
            parent=styles['Heading1'],
            fontSize=24,
            spaceAfter=20,
            textColor=colors.HexColor("#4A4E69")
        )
        
        insight_style = ParagraphStyle(
            name="InsightText",
            parent=styles['Normal'],
            fontSize=12,
            leading=16,
            spaceAfter=30,
            textColor=colors.HexColor("#22223B")
        )

        # 1. Title
        elements.append(Paragraph("QuerySense BI - Executive Summary", title_style))
        
        # 2. Insights
        elements.append(Paragraph("<b>Executive Summary & Overview:</b>", styles['Heading3']))
        elements.append(Spacer(1, 5))
        elements.append(Paragraph(insights, insight_style))
        
        # 3. Dataset Metrics
        elements.append(Paragraph("<b>Dataset Metrics:</b>", styles['Heading3']))
        metrics_text = f"Total Rows: {len(dataframe)} | Total Columns: {len(dataframe.columns)}"
        elements.append(Paragraph(metrics_text, insight_style))
        
        # 4. Data Preview Table (Top 15 rows)
        elements.append(Paragraph("<b>Data Preview (Top 15 Rows):</b>", styles['Heading3']))
        elements.append(Spacer(1, 10))
        
        # Convert DataFrame to a list of lists for ReportLab
        # Convert all to strings to avoid rendering issues
        df_preview = dataframe.head(15).astype(str)
        table_data = [df_preview.columns.values.tolist()] + df_preview.values.tolist()
        
        # Create Table
        t = Table(table_data)
        
        # Add Premium Styling
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#667EEA")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#F8F9FA")),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor("#22223B")),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor("#F1F3F5")])
        ]))
        
        elements.append(t)
        
        # Build the PDF
        doc.build(elements)
        return output_path
    except Exception as e:
        logger.error(f"Failed to generate PDF report: {e}")
        raise
