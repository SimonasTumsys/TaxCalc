from PyPDF2 import PdfFileReader
import pdftotext


path = r"C:\Users\PC\Desktop\Coding\Python\TaxCalc\2021-04-26 -- 2021-05-03 Simonas Tumsys Weekly Report.pdf"
fixed_path = path.replace('\\', '/')

pdf = open(fixed_path, 'rb')
pdfReader = PdfFileReader(pdf)

print("PDF File name: " + str(pdfReader.getDocumentInfo().title))

bf_obj = {path:"text"}

numOfPages = pdfReader.getNumPages()

for i in range(0, numOfPages):
    print("Page Number: " + str(i))
    print("- - - - - - - - - - - - - - - - - - - -")
    pageObj = pdfReader.getPage(i)
    print(pageObj.extractText())
    print("- - - - - - - - - - - - - - - - - - - -")
# close the PDF file object
pdf.close()