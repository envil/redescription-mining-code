#!/bin/bash

echo "<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>Index of /${1##*/}</title>
</head>
<body>

<h1>Index of /${1##*/}</h1>

<ul>"

for l in $(ls -1 --group-directories-first  $1); do
 echo "<li><a href=\"./${l##*/}\">${l##*/}</a></li>"
done

echo "</ul>
</body>
</html>"
