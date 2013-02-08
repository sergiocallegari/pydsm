# -*- coding: utf-8 -*-

# Copyright (c) Sergio Callegari, Federico Bizzarri 2012
# All rights reserved.

"""Demo for DS modulator with first order LP filter.

Copyright (c) Sergio Callegari, Federico Bizzarri 2012
All rights reserved.
"""

import numpy as np
import scipy as sp
__import__("scipy.signal")
import matplotlib.pyplot as plt
from pydsm.ir import impulse_response
from pydsm.delsig import synthesizeNTF, simulateDSM, evalTF
from pydsm.delsig import dbv, dbp
from pydsm.NTFdesign.filter_based import quantization_noise_gain, \
    synthesize_ntf_from_filter_ir

# Signal specification
fsig=1000.
B=1000.
OSR=1024
fphi=B*OSR*2
# Lee constraint
H_inf=1.5
# FIR Order for optimal NTF
order=12
# Signal amplitude
A=0.5

# Generate filter. Transfer function is normalized to be 0dB in pass band
# As an example, take cutoff freq at twice the top of the signal band to avoid
# attenuation when the input signal is close to it.
print("...generating filter")
# Care: in butter the cut of frequency is specified as a number from 0 to 1
# where 1 is fphi/2, not fphi
hz=sp.signal.butter(1, 2*(2*B)/fphi, btype='low')

# Compute impulse response
print("...computing impulse response of filter")
hz_ir=impulse_response(hz, db=60)

# Compute the optimal NTF
print("... computing optimal NTF")
ntf_opti=synthesize_ntf_from_filter_ir(order, hz_ir, H_inf=H_inf)

# Compute an NTF with DELSIG, for comparison
print("... computing delsig NTF")
ntf_delsig=synthesizeNTF(4, OSR, 3, H_inf, 0)

# Determine freq values for which plots are created
fmin=10**np.ceil(np.log10(2*B/OSR))
fmax=10**np.floor(np.log10(fphi/2))
ff=np.logspace(np.log10(fmin),np.log10(fmax),1000)

# Compute frequency response data
resp_filt=np.abs(evalTF(hz,np.exp(1j*2*np.pi*ff/fphi)))
resp_opti=np.abs(evalTF(ntf_opti,np.exp(1j*2*np.pi*ff/fphi)))
resp_delsig=np.abs(evalTF(ntf_delsig,np.exp(1j*2*np.pi*ff/fphi)))

# Plot frequency response
plt.figure()
plt.semilogx(ff,dbv(resp_filt), 'b', label="Output filter")
plt.semilogx(ff,dbv(resp_opti), 'r', label="Optimal NTF")
plt.semilogx(ff,dbv(resp_delsig), 'g', label="Delsig NTF")
plt.legend(loc="lower right")
plt.suptitle("Output filter and NTFs")

# Check merit factors
ffl=np.linspace(fmin, fmax, 1000)
pg_opti=np.abs(evalTF(ntf_opti,np.exp(1j*2*np.pi*ffl/fphi)))* \
    np.abs(evalTF(hz,np.exp(1j*2*np.pi*ffl/fphi)))
pg_delsig=np.abs(evalTF(ntf_delsig,np.exp(1j*2*np.pi*ffl/fphi)))* \
    np.abs(evalTF(hz,np.exp(1j*2*np.pi*ffl/fphi)))
plt.figure()
plt.plot(ffl,pg_opti**2,'r', label="Optimal NTF")
plt.plot(ffl,pg_delsig**2,'g', label="Delsig NTF")
plt.legend(loc="upper right")
plt.suptitle("Merit factor integrand")

# Compute expected behavior
sigma2_e=1./3
noise_power_opti_1=quantization_noise_gain(hz, ntf_opti)*sigma2_e
noise_power_delsig_1=quantization_noise_gain(hz, ntf_delsig)*sigma2_e
print("Expected optimal noise level {} ({} dB).\nExpected SNR {} dB".format( \
    noise_power_opti_1, dbp(noise_power_opti_1), \
        dbp(0.5*A**2)-dbp(noise_power_opti_1)))
print("Expected delsig noise level {} ({} dB).\nExpected SNR {} dB".format( \
    noise_power_delsig_1, dbp(noise_power_delsig_1),\
        dbp(0.5*A**2)-dbp(noise_power_delsig_1)))

# Start and stop time for DS simulation
Tstop=100E3
Tstart=40E3
dither_sigma=1e-6

# Set up DSM simulation
tt=np.asarray(xrange(int(Tstop)))
uu=A*np.sin(2*np.pi*fsig/fphi*tt)
dither=np.random.randn(len(uu))*dither_sigma
uud=uu+dither

# Simulate the DSM
print("Simulating optimal NTF")
xx_opti = simulateDSM(uud, ntf_opti)[0]
print("Simulating delsig NTF")
xx_delsig = simulateDSM(uud, ntf_delsig)[0]

print("Applying the output filter")
uu_filt=sp.signal.lfilter(hz[0],hz[1],uu)
xx_opti_filt=sp.signal.lfilter(hz[0],hz[1],xx_opti)
xx_delsig_filt=sp.signal.lfilter(hz[0],hz[1],xx_delsig)

plt.figure()
plt.plot(tt[Tstart:Tstart+4*OSR],uu_filt[Tstart:Tstart+4*OSR],'b',\
    label="Filtered input")
plt.plot(tt[Tstart:Tstart+4*OSR],xx_opti_filt[Tstart:Tstart+4*OSR],'r',\
    label="Filtered Optimal DSM output")
plt.plot(tt[Tstart:Tstart+4*OSR],xx_delsig_filt[Tstart:Tstart+4*OSR],'g', \
    label="Filtered Delsig DSM output")
plt.legend(loc="best")
plt.suptitle("Portion of time domain behavior")

print("Filtering input")
uud_filt=sp.signal.lfilter(hz[0],hz[1],uud)

noise_power_opti_2=np.sum((uud_filt[Tstart:]-xx_opti_filt[Tstart:])**2)/ \
    (Tstop-Tstart)
noise_power_delsig_2=np.sum((uud_filt[Tstart:]-xx_delsig_filt[Tstart:])**2)/ \
    (Tstop-Tstart)

print("Observed optimal noise level {} ({} dB)\nObserved SNR {} dB".format( \
    noise_power_opti_2, dbp(noise_power_opti_2), \
        dbp(0.5*A**2)-dbp(noise_power_opti_2)))
print("Observed delsig noise level {} ({} dB)\nObserved SNR {} dB".format( \
    noise_power_delsig_2, dbp(noise_power_delsig_2), \
        dbp(0.5*A**2)-dbp(noise_power_delsig_2)))

plt.show()