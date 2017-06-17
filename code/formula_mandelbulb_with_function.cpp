void MandelbulbIteration(CVector4 &z, const sFractal *fractal, sExtendedAux &aux)
{
	double th0 = asin(z.z / aux.r) + fractal->bulb.betaAngleOffset;
	double ph0 = atan2(z.y, z.x) + fractal->bulb.alphaAngleOffset;
	double rp = pow(aux.r, fractal->bulb.power - 1.0);
	double th = th0 * fractal->bulb.power;
	double ph = ph0 * fractal->bulb.power;
	double cth = cos(th);
	aux.r_dz = (rp * aux.r_dz) * fractal->bulb.power + 1.0;
	rp *= aux.r;
	z.x = cth * cos(ph) * rp;
	z.y = cth * sin(ph) * rp;
	z.z = sin(th) * rp;
}

