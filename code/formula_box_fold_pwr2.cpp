//box fold
if (fabs(z.x) > fractal->foldingIntPow.foldFactor)
	z.x = sign(z.x) * fractal->foldingIntPow.foldFactor
		 * 2.0 - z.x;
if (fabs(z.y) > fractal->foldingIntPow.foldFactor)
	z.y = sign(z.y) * fractal->foldingIntPow.foldFactor
		 * 2.0 - z.y;
if (fabs(z.z) > fractal->foldingIntPow.foldFactor)
	z.z = sign(z.z) * fractal->foldingIntPow.foldFactor
		 * 2.0 - z.z;

//spherical fold
double fR2_2 = 1.0;
double mR2_2 = 0.25;
double r2_2 = z.Dot(z);
double tglad_factor1_2 = fR2_2 / mR2_2;

if (r2_2 < mR2_2)
{
	z = z * tglad_factor1_2;
}
else if (r2_2 < fR2_2)
{
	double tglad_factor2_2 = fR2_2 / r2_2;
	z = z * tglad_factor2_2;
}

//Mandelbulb power 2
z = z * 2.0;
double x2 = z.x * z.x;
double y2 = z.y * z.y;
double z2 = z.z * z.z;
double temp = 1.0 - z2 / (x2 + y2);
zTemp.x = (x2 - y2) * temp;
zTemp.y = 2.0 * z.x * z.y * temp;
zTemp.z = -2.0 * z.z * sqrt(x2 + y2);
z = zTemp;
z.z *= fractal->foldingIntPow.zFactor;
