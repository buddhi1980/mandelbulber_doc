void cFractalMandelbulb::FormulaCode(CVector4 &z, const sFractal *fractal, sExtendedAux &aux)
{
	const double th0 = asin(z.z / aux.r) + fractal->bulb.betaAngleOffset;
	const double ph0 = atan2(z.y, z.x) + fractal->bulb.alphaAngleOffset;
	double rp = pow(aux.r, fractal->bulb.power - 1.0);
	const double th = th0 * fractal->bulb.power;
	const double ph = ph0 * fractal->bulb.power;
	const double cth = cos(th);
	aux.DE = (rp * aux.DE) * fractal->bulb.power + 1.0;
	rp *= aux.r;
	z.x = cth * cos(ph) * rp;
	z.y = cth * sin(ph) * rp;
	z.z = sin(th) * rp;
}
