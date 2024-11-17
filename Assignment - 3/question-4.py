from bs4 import BeautifulSoup
import re

html = """
<html>
<head>
<title>My first web page</title>
</head>
<body>
<h1>My first web page</h1>
<h2>What this is tutorial</h2>
<p>A simple page put together using HTML. <em>I said a simple page.</em>.</p>
<ul>
    <li>To learn HTML</li>
    <li>
        To show off
        <ol>
            <li>To my boss</li>
            <li>To my friends</li>
        </ol>
    </li>
    <li>Because I have fallen in love with my computer and want to give her some HTML loving.</li>
</ul>
<h3>Where to find the tutorial</h3>
<p><a href="http://www.aaa.com"><img src=http://www.aaa.com/badge1.gif></a></p>
<h4>Some random table</h4>
<table>
    <tr class="tutorial1">
        <td>Row 1, cell 1</td>
        <td>Row 1, cell 2<img src=http://www.bbb.com/badge2.gif></td>
        <td>Row 1, cell 3</td>
    </tr>
    <tr class="tutorial2">
        <td>Row 2, cell 1</td>
        <td>Row 2, cell 2</td>
        <td>Row 2, cell 3<img src=http://www.ccc.com/badge3.gif></td>
    </tr>
</table>
</body>
</html>
"""



# a. Page title
print(BeautifulSoup(html, 'html.parser').title.text)

# b. Second list item under "To show off"
print(BeautifulSoup(html, 'html.parser').find_all('ol')[0].find_all('li')[1].text)

# c. All <td> tags in the first row of the table
print([td.text for td in BeautifulSoup(html, 'html.parser').find('table').find_all('tr')[0].find_all('td')])

# d. <h2> headings with "tutorial"
print([h2.text for h2 in BeautifulSoup(html, 'html.parser').find_all('h2', string=re.compile(r'tutorial'))])

# e. Text containing "HTML"
print([text for text in BeautifulSoup(html,'html.parser').find_all(string=re.compile(r'HTML'))])

# f. Text in the second row of the table
print([td.text for td in BeautifulSoup(html, 'html.parser').find('table').find_all('tr')[1].find_all('td')])

# g. All <img> tags in the table
print([img['src'] for img in BeautifulSoup(html, 'html.parser').find('table').find_all('img')])
