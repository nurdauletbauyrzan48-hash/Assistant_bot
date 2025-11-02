import os
import subprocess
from docx import Document
import pandas as pd
import mimetypes
from PIL import Image
import pytesseract
import PyPDF2
import logging
import re

logger = logging.getLogger('TelegramBot')

class FileProcessor:
    """Handle different file types and conversions"""

    @staticmethod
    def detect_file_type(file_path):
        """Detect the type of file"""
        try:
            mime_type, _ = mimetypes.guess_type(file_path)
            logger.info(f"Анықталған файл түрі: {mime_type}")
            return mime_type
        except Exception as e:
            logger.error(f"Файл түрін анықтау кезінде қате: {str(e)}")
            return None

    @staticmethod
    def convert_doc_to_txt(input_path, output_path):
        """Convert DOC/DOCX to TXT"""
        try:
            logger.info(f"DOC/DOCX файлын өңдеу басталды: {input_path}")

            # Check if it's an old .doc file
            if input_path.lower().endswith('.doc'):
                try:
                    # Try to use antiword for old .doc files
                    result = subprocess.run(['antiword', input_path], capture_output=True, text=True)
                    if result.returncode == 0:
                        with open(output_path, "w", encoding="utf-8") as file:
                            file.write(result.stdout)
                        logger.info("DOC файлы antiword арқылы сәтті өңделді")
                        return
                    else:
                        logger.warning("Antiword қате қайтарды, python-docx қолданып көреміз")
                except Exception as e:
                    logger.warning(f"Antiword қатесі: {str(e)}, python-docx қолданып көреміз")

            # If not .doc or antiword failed, try python-docx
            doc = Document(input_path)
            lines = []
            for para in doc.paragraphs:
                text = para.text.strip()
                if text:  # Skip empty lines
                    lines.append(text)

            with open(output_path, "w", encoding="utf-8") as file:
                file.write("\n".join(lines))
            logger.info("DOC/DOCX файлы сәтті өңделді")
        except Exception as e:
            logger.error(f"DOC/DOCX файлын өңдеу кезінде қате: {str(e)}")
            raise Exception(f"DOC/DOCX файлын өңдеу кезінде қате: {str(e)}")

    @staticmethod
    def convert_image_to_txt(input_path, output_path):
        """Convert image to text using OCR"""
        try:
            logger.info(f"Суретті өңдеу басталды: {input_path}")
            image = Image.open(input_path)
            text = pytesseract.image_to_string(image, lang='kaz+rus+eng')  # Support multiple languages
            with open(output_path, "w", encoding="utf-8") as file:
                file.write(text)
            logger.info("Сурет сәтті өңделді")
        except Exception as e:
            logger.error(f"Суретті өңдеу кезінде қате: {str(e)}")
            raise Exception(f"Суретті өңдеу кезінде қате: {str(e)}")

    @staticmethod
    def convert_excel_to_txt(input_path, output_path):
        """Convert Excel to TXT"""
        try:
            logger.info(f"Excel файлын өңдеу басталды: {input_path}")
            df = pd.read_excel(input_path)
            df.to_csv(output_path, index=False, sep='\t', encoding='utf-8')
            logger.info("Excel файлы сәтті өңделді")
        except Exception as e:
            logger.error(f"Excel файлын өңдеу кезінде қате: {str(e)}")
            raise Exception(f"Excel файлын өңдеу кезінде қате: {str(e)}")

    @staticmethod
    def convert_pdf_to_txt(input_path, output_path):
        """Convert PDF to TXT"""
        try:
            logger.info(f"PDF файлын өңдеу басталды: {input_path}")
            with open(input_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = []
                for page in pdf_reader.pages:
                    text.append(page.extract_text())

            with open(output_path, "w", encoding="utf-8") as file:
                file.write("\n".join(text))
            logger.info("PDF файлы сәтті өңделді")
        except Exception as e:
            logger.error(f"PDF файлын өңдеу кезінде қате: {str(e)}")
            raise Exception(f"PDF файлын өңдеу кезінде қате: {str(e)}")

    @staticmethod
    def process_file(input_path, output_path):
        """Process text file to required format"""
        try:
            logger.info(f"Мәтінді өңдеу басталды: {input_path}")
            with open(input_path, "r", encoding="utf-8") as file:
                lines = file.readlines()

            processed_lines = []
            first_variant = True
            in_question = False

            for line in lines:
                line = line.strip()
                if not line:  # Skip empty lines
                    continue

                # Check for numbered questions (e.g., "120.", "121.", etc.)
                numbered_question = re.match(r'^\d+\.(.+)$', line)

                if numbered_question:
                    # It's a numbered question
                    processed_lines.append("? " + numbered_question.group(1).strip())
                    first_variant = True
                    in_question = True
                elif line.startswith("<variant>"):
                    if first_variant and in_question:
                        processed_lines.append("+ " + line.replace("<variant>", "").strip())
                        first_variant = False
                    else:
                        processed_lines.append("- " + line.replace("<variant>", "").strip())
                elif line.startswith("<question>"):
                    processed_lines.append("? " + line.replace("<question>", "").strip())
                    first_variant = True
                    in_question = True
                else:
                    # If it's not a question or variant, treat it as regular text
                    processed_lines.append(line)
                    in_question = False

            with open(output_path, "w", encoding="utf-8") as file:
                file.write("\n".join(processed_lines))
            logger.info("Мәтін сәтті өңделді")
        except Exception as e:
            logger.error(f"Мәтінді өңдеу кезінде қате: {str(e)}")
            raise Exception(f"Мәтінді өңдеу кезінде қате: {str(e)}")