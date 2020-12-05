import pypandoc

# output = pypandoc.convert_file('1.html', 'md', outputfile="file1.md")
# output = pypandoc.convert_file('1.html', 'docx', outputfile="file2.docx")
output = pypandoc.convert_file('file1.md', 'ppt', outputfile="file1.ppt")
