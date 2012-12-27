import pynbody
import numpy as np

correct_pos_3000 = np.array([[ -6.81076660e+02,  -7.23552307e+02,  -7.25669434e+02],
       [ -6.71421432e+00,   1.49479971e+01,  -2.68915343e+00],
       [  2.51839962e+01,   4.55662251e+00,   8.47755241e+00],
       [ -1.00104582e+00,  -6.07526116e-02,  -1.49165303e-01],
       [ -2.04572430e+01,   1.03648460e+02,   5.03591309e+01],
       [ -5.80246925e+01,  -1.66332428e+02,  -2.29324055e+00],
       [  1.36629379e+02,   1.65108871e+02,  -3.35499916e+01],
       [  1.48270607e+01,  -1.23228998e+01,   3.34462318e+01],
       [  6.51616364e+01,   1.20620003e+02,  -7.77010441e+00],
       [  1.65806985e+00,  -1.41221046e+00,  -6.71795487e-01],
       [ -1.15322161e+01,  -1.51604004e+02,   2.80298443e+01],
       [  3.09369621e+01,  -6.83208466e+00,  -4.56447563e+01],
       [  1.91674484e+02,  -1.55248932e+02,   1.04276825e+02],
       [ -1.04876442e+02,   7.76101990e+01,  -6.30369377e+00],
       [  8.45507050e+01,   1.95127396e+02,   3.00925674e+01],
       [  1.77649445e+02,  -7.40343704e+01,  -5.14584045e+01],
       [  1.75948318e+02,  -4.35685616e+01,  -6.03500099e+01],
       [ -2.90256286e+00,  -1.42134070e-01,  -2.45711654e-01],
       [  2.03460503e+01,  -3.19464374e+00,  -1.51950226e+01],
       [ -1.10691252e+01,  -3.98053360e+01,   3.24721260e+01],
       [ -7.91164932e+01,   7.75931091e+01,   2.01976913e+02],
       [ -5.57837753e+01,  -9.54266250e-01,   2.70661087e+01],
       [  4.70552063e+01,  -1.51884377e+00,  -2.91022644e+01],
       [  1.66740036e+01,   1.21764809e+02,   5.77328131e-02],
       [ -1.14060152e+00,  -1.94306965e+01,   6.05390892e+01],
       [ -1.71269822e+00,   5.36839104e+00,  -1.03770185e+00],
       [  6.45761490e+00,  -9.43726897e-02,   1.55888367e-02],
       [ -6.63572235e+01,  -5.26198120e+01,   9.14764633e+01],
       [ -5.11834793e+01,  -1.42530243e+02,  -3.47918396e+01],
       [ -4.96904449e+01,  -8.24150925e+01,  -4.58002396e+01],
       [  1.92305359e+02,  -1.03764086e+01,  -1.58101181e+02],
       [ -4.35308903e-01,   2.99998522e+00,   8.72876525e-01],
       [ -1.07969940e+00,  -8.92009616e-01,  -5.08299470e-01],
       [ -6.55018032e-01,   2.55334854e-01,  -2.30630562e-01],
       [  8.35401535e-01,   8.87062177e-02,  -3.50615680e-01],
       [ -1.35528529e+00,   5.64608872e-01,  -1.99165419e-01],
       [ -1.00380623e+00,   6.14328422e-02,  -3.87546539e-01],
       [  1.61206961e-01,  -1.60035312e-01,  -2.58585483e-01],
       [ -1.07256079e+00,   1.22600794e-01,  -7.59867504e-02],
       [  1.38124004e-01,  -8.36208403e-01,  -5.24163544e-01],
       [ -4.31075096e+00,  -4.68401575e+00,  -5.49619913e-01],
       [ -1.08389962e+00,  -2.39896238e-01,  -1.85273886e-01],
       [  4.59061813e+00,   4.45952606e+00,  -4.76922780e-01],
       [  2.31774628e-01,   3.79601568e-01,  -1.34110510e-01],
       [  3.22907194e-02,   4.13152128e-01,  -1.84739470e-01],
       [  1.86674702e+00,  -1.44239044e+02,   1.74692688e+02],
       [ -9.60105743e+01,  -1.80999908e+02,   3.58957458e+02],
       [  1.84442310e+01,   4.51696472e+01,  -1.26225410e+02],
       [ -1.70472504e+02,  -1.81023392e+02,  -3.95618553e+01],
       [  1.51610352e+02,   5.92312622e+01,   1.38243818e+01],
       [ -9.39944305e+01,  -5.65567894e+01,   6.03508224e+01],
       [  2.12093544e+01,   1.69410915e+01,   1.70963898e+01],
       [  9.02289658e+01,   5.09941053e+00,   3.90569534e+01],
       [ -6.67528915e+01,  -5.71347809e+01,  -1.71120056e+02],
       [ -8.49080048e+01,  -1.23809166e+02,   1.49720718e+02],
       [ -8.37564697e+01,  -2.31880608e+01,   1.03829887e+02],
       [ -5.09666290e+01,  -7.67966156e+01,   5.11046524e+01],
       [  8.67601681e+00,  -2.49246979e+01,   1.02630615e+01],
       [ -1.05194492e+01,   5.32438889e+01,   2.97180634e+01],
       [  3.25910980e+02,  -2.86987152e+02,   1.35943520e+00],
       [ -9.27782249e+00,   3.88515282e+01,   1.57459183e+02],
       [ -8.28347969e+00,   1.91837668e+00,  -1.33861208e+00],
       [ -1.02203316e+02,  -1.97741699e+02,  -7.81557922e+01],
       [ -4.26288261e+01,   5.69040565e+01,  -4.09044342e+02],
       [ -2.22998619e+00,  -3.28176904e+00,  -5.18244314e+00],
       [  1.40447197e+01,  -8.95229149e+00,   2.44229603e+01],
       [  7.87872009e+01,   7.57512207e+01,   1.39982224e+02],
       [ -3.86397209e+01,  -2.96485119e+01,  -3.82425804e+01],
       [  4.07511215e+01,   3.69774513e+01,  -3.46264191e+01],
       [ -4.78107376e+01,  -4.97248421e+01,  -2.93378353e+00],
       [ -1.69243240e+01,  -1.17719440e+01,  -2.11776047e+01],
       [  2.16464890e+02,   3.13867462e+02,  -1.87175095e+02],
       [ -1.32231588e+01,  -6.87708664e+00,   1.28819923e+01],
       [  2.00511742e+01,  -5.61033010e-01,   1.83038788e+01],
       [ -5.42057304e+01,   2.68252258e+01,   1.08439209e+02],
       [ -4.02714081e+01,  -3.03690277e+02,   3.57707947e+02],
       [ -8.42256470e+01,   1.82991302e+02,   2.26604630e+02],
       [ -7.14998169e+01,  -1.50979782e+02,   1.94897404e+01]])

def setup() :
    global f
    f = pynbody.load("testdata/nchilada_test/12M.00001")
   
    
def test_get() :
    current = f['pos'][::3000]
    print repr(current)
    print f._family_slice
    assert (np.abs(current-correct_pos_3000).mean()<1.e-6)


def test_get_gas() :
    correct = [  2.23225154e-08,   1.19859905e-07,   8.66461534e-08,
         1.36909285e-03,   2.11048416e-07,   2.63381509e-07,
         2.98710262e-07,   1.08983599e-07,   1.07130404e-07,
         7.49599457e-01,   2.05589359e-07,   1.20924241e-07,
         1.72308305e-07,   1.82599763e-07,   1.91588853e-07,
         1.55311682e-07,   2.24381495e-07,   7.48850703e-01,
         3.63184469e-08,   9.44389882e-08,   1.55873153e-07,
         1.49604929e-07,   1.38858326e-07,   1.57812593e-07,
         1.15718933e-07,   7.49949515e-01,   7.47042358e-01,
         1.99594979e-07,   2.19145448e-07,   6.16430157e-07,
         4.46814852e-07]
    current = f.gas['HI'][::3000]

    print repr(current)

    
    assert (np.abs(current-correct).sum()<1.e-9)


def test_array_completion_unit_sanity() :
    del f['pos']

    f.gas['pos']
    assert 'pos' not in f

    f.gas['pos'].convert_units("Mpc")
    f.star['pos'].convert_units("pc")

    assert (np.abs(f['pos'][::3000]-correct_pos_3000).mean()<1.e-6)
    