cFractalMandelbulb::cFractalMandelbulb() : cAbstractFractal()
{
	nameInComboBox = "Mandelbulb";
	internalName = "mandelbulb";
	internalID = fractal::mandelbulb;
	DEType = analyticDEType;
	DEFunctionType = logarithmicDEFunction;
	cpixelAddition = cpixelEnabledByDefault;
	defaultBailout = 10.0;
	DEAnalyticFunction = analyticFunctionLogarithmic;
	coloringFunction = coloringFunctionDefault;
}
