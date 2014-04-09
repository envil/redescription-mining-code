<?xml version="1.0"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
<xsl:template match="root">
<html> 
<head>
<title>SIREN &#8212; Interactive and visual redescription mining</title>
<link rel="stylesheet" type="text/css" href="./siren.css"/>
</head>
<body>

<div class="page-header">
<p><xsl:value-of select="info"/></p>

<p>
This is a list of available parameters listed by section in the form: 
<span class="parameter-name">[parameter name = default value]</span>
</p>
</div>

<xsl:for-each select="section">
	<h2 class="section"><xsl:value-of select="name"/></h2>
	<ul>
	<xsl:for-each select="section/parameter[parameter_type='open']">
		<li>  		
		<h4 class="parameter-label"><xsl:value-of select="label"/></h4>
		<span class="parameter-name">[<xsl:value-of select="name"/> =
		<xsl:value-of select="default/value"/>]
		</span>
		<p class="parameter-legend"><xsl:value-of select="legend"/>
		(<span class="parameter-details"><xsl:value-of select="value_type"/></span>)
		</p>
		</li>
	</xsl:for-each>
	<xsl:for-each select="section/parameter[parameter_type='range']">
		<li>  		
		<h4 class="parameter-label"><xsl:value-of select="label"/></h4>
		<span class="parameter-name">[<xsl:value-of select="name"/> =
		<xsl:value-of select="default/value"/>]
		</span>
		<p class="parameter-legend"><xsl:value-of select="legend"/>
		(<span class="parameter-details"><xsl:value-of select="value_type"/> in range [<xsl:value-of select="range_min"/> , <xsl:value-of select="range_max"/>]</span>)
		</p>		
		</li>
	</xsl:for-each>
	<xsl:for-each select="section/parameter[parameter_type='single_options']">
		<li>  		
		<h4 class="parameter-label"><xsl:value-of select="label"/></h4>
		<span class="parameter-name">[<xsl:value-of select="name"/> =
		<xsl:value-of select="default/value"/>]
		</span>
		<p class="parameter-legend"><xsl:value-of select="legend"/>
		(<span class="parameter-details">Single choice among: 
		<xsl:for-each select="options/value">
			<xsl:value-of select="."/>
			<xsl:if test="position() != last()">, </xsl:if>
		</xsl:for-each>
		</span>)
		</p>
		</li>
	</xsl:for-each>
	<xsl:for-each select="section/parameter[parameter_type='multiple_options']">
		<li>  		
		<h4 class="parameter-label"><xsl:value-of select="label"/></h4>
		<span class="parameter-name">[<xsl:value-of select="name"/> =
		<xsl:for-each select="default/value">
			<xsl:value-of select="."/>
			<xsl:if test="position() != last()">, </xsl:if>
		</xsl:for-each>]
		</span>
		<p class="parameter-legend"><xsl:value-of select="legend"/>
		(<span class="parameter-details">Multiple choices among: 
		<xsl:for-each select="options/value">
			<xsl:value-of select="."/>
			<xsl:if test="position() != last()">, </xsl:if>
		</xsl:for-each>
		</span>)
		</p>
		</li>
	</xsl:for-each>
	</ul>
</xsl:for-each>

</body>
</html>
</xsl:template>

</xsl:stylesheet>
