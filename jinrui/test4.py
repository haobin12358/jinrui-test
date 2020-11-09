import mammoth

result = mammoth.convert_to_html(open("C:\\Users\\Administrator\\Desktop\\test\\1\\数学  推演卷（一） A卷.docx", "rb"))

html = result.value
messages = result.messages
print(html)

