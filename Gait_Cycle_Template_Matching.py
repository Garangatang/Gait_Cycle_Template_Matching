"""
Description: This class contains code for generate a template which can be used to mark all inflection 
    points on a large underfoot pressure dataset. These inflection points can then be used to parse
    underfoot pressure data into complete gait cycles.

Written by Grange Simpson
Version: 2024.12.15

Usage: Load the dictionary in the .pkl file output from Manual_Inflection_Point_Marking_GUI.py, or another 
    dictionary which contains value: dataset name, key: dataset inflection points separately. 

    Important: Only function which needs to be interacted with in this class is find_template_extract_inds().
Recommendations: 
"""

import numpy as np
from math import factorial
from scipy import interpolate

# Template matching algorithm for finding inflection point
class Template_Matching:
    """
    Description: Holds data, and linked structs.

    param: templateArr: Nx200 matrix to hold all 200 value arrays constructed from each input inflection point,
            where N = number of input inflection points.
    param: template: Saved template constructed by taking the average of each column to create a 1x200 array.
    param: overlapVals: Overlap values created when iterating the template across the underfoot pressure data.
    param: overlapIndicesBuffer: Buffer of index values matching to the buffer of overlap values. Used for
        marking the inflection point index within each overlapValBuffer.
    param: overlapValBuffer: Buffer of values as the template approaches and passes over an inflection point.
    param: keptOverlapIndices: Maximum overlapIndices from each overlapValBuffer kept to be matched back onto
        the underfoot pressure data.
    param: upperInflPointRange: Number of values to be kept after each inflection point when building the
        template.
    param: lowerInflPointRange: Number of values to be kept before each each inflection point when building the
        template.
    """
    def __init__(self):
        self.templateArr = np.array([])
        self.template = 0
        self.template = 0
        self.overlapVals = np.array([])

        self.overlapIndicesBuffer = np.array([])
        self.overlapValBuffer = np.array([])

        self.keptOverlapIndices = np.array([])

        self.upperInflPointRange = 100
        self.lowerInflPointRange = 100

        self.inflPointDict = {}

    """
    Description: Input data is upsampled and interpolated to match desired sampling frequency.

    param: x: X-axis data to be upsampled.
    param: y: y-axis data to be upsampled.
    param: inlectionIndices: manually marked inflection point indices which need to be mapped back onto the
        upsampled data.
    param: upSampleFactor: The length factor that the data needs to be upsampled by. Example: If the data is 
        originally sampled at 66 Hz, and needs to be upsampled to 1980 Hz, then the upsampleFactor is 30.
    """
    def upsample_with_inflections(self, x, y, inflectionIndices, upsampleFactor):
        # Create a boolean mask for inflection points
        inflectionMask = np.zeros(len(x), dtype=bool)
        inflectionMask[inflectionIndices] = True
        
        # Create new x values for upsampled data
        xNew = np.linspace(x.min(), x.max(), len(x) * upsampleFactor)
        
        # Interpolate the data
        f = interpolate.interp1d(x, y, kind='cubic')
        yNew = f(xNew)
        
        # Find the new indices for inflection points
        newInflectionIndices = np.searchsorted(xNew, x[inflectionMask])
        
        # Ensure inflection points are preserved
        yNew[newInflectionIndices] = y[inflectionMask]
        
        return xNew, yNew, newInflectionIndices

    """
    Description: Savitzky golay algorithm is used to smooth out the very spiky upsampled data using a running 
        average

    param: y: array_like, shape (N,) the values of the time history of the signal.
    param: window_size: int, the length of the window. Must be an odd integer number.
    param: order: int, the order of the polynomial used in the filtering. Must be less then `window_size` - 1.
    deriv: int, the order of the derivative to compute (default = 0 means only smoothing)
    Returns
    -------
    ys : ndarray, shape (N), the smoothed signal (or it's n-th derivative).
    """
    def savitzky_golay(self, y, window_size, order, deriv=0, rate=1):

        try:
            window_size = np.abs(int(window_size))
            order = np.abs(int(order))

        except ValueError as msg:
            raise ValueError("window_size and order have to be of type int")
        
        if window_size % 2 != 1 or window_size < 1:
            raise TypeError("window_size size must be a positive odd number")
        
        if window_size < order + 2:
            raise TypeError("window_size is too small for the polynomials order")
        
        order_range = range(order+1)
        half_window = (window_size -1) // 2
        # Precompute coefficients
        b = np.mat([[k**i for i in order_range] for k in range(-half_window, half_window+1)])
        m = np.linalg.pinv(b).A[deriv] * rate**deriv * factorial(deriv)
        # Pad the signal at the extremes with
        # Values taken from the signal itself
        firstvals = y[0] - np.abs( y[1:half_window+1][::-1] - y[0] )
        lastvals = y[-1] + np.abs(y[-half_window-1:-1][::-1] - y[-1])
        y = np.concatenate((firstvals, y, lastvals))
        
        return np.convolve( m[::-1], y, mode='valid')
    
    """
    Description: Use the input pressure data to extract 200 value templates at each input inflection point.

    param: inputIndices: Manually marked inflection point indices to be used in extracting templates from
        inputPressData
    param: inputPressData: Underfoot pressure data which corresponds to the input manually marked inflection
        points.
    """
    def extract_template(self, inputIndices, inputPressData):
        # Iterate through the input indices and pull the 100 values below and above the manually marked inflection point
        for i in range(len(inputIndices)):
            try:
                if (len(self.templateArr) == 0):
                    self.templateArr = inputPressData[int(inputIndices[i] - self.lowerInflPointRange):int(inputIndices[i] + self.upperInflPointRange)]
                else:
                        self.templateArr = np.vstack((self.templateArr, inputPressData[int(inputIndices[i] - self.lowerInflPointRange):int(inputIndices[i] + self.upperInflPointRange)]))
            except Exception as e:
                    print(e)

        self.template = np.mean(self.templateArr, axis = 0)

    """
    Description: Iterate self.template across all underfoot pressure data and extract the inflection points

    param: inputPressData: Underfoot pressure data which will have the template iterated across it.
    param: signalIncreaseVal: Amount to positively shift the overlap signal on the y-axis after reflecting
        it across the x-axis.
    """
    def find_infl_using_template(self, inputPressData, signalIncreaseVal):
        for i in range(len(inputPressData) - 2):
            try:
                if (i > len(self.template) and i < len(inputPressData) - len(self.template)):
                    # Extract a segment of data from the input pressure data and see how it matches up with 
                    # the template
                    pressDataSegm = inputPressData[i:i + len(self.template)]
                    # Calculating sum absolute value difference for creating the overlap signal.
                    overlapVal = np.sum(np.abs(pressDataSegm - self.template))
                    overlapVal = (-overlapVal) + signalIncreaseVal
                    self.overlapVals = np.append(self.overlapVals, overlapVal)

                    # If threshold condition is met, start adding the overlap values to the buffer
                    if (overlapVal > 0):
                        self.overlapValBuffer = np.append(self.overlapValBuffer, overlapVal)    
                        self.overlapIndicesBuffer = np.append(self.overlapIndicesBuffer, i - len(self.template))
                        self.overlapIndices = np.append(self.overlapIndices, i - len(self.template))

                    # Extracting values from the buffer and clearing it if moving on to the next inflection point
                    else:
                        if (len(self.overlapValBuffer) > 0):
                            # finding the minimum value within the buffered overlap values
                            maxIndex = np.where(self.overlapValBuffer == np.max(self.overlapValBuffer))
                            maxOverlapPoint = self.overlapIndicesBuffer[maxIndex[0]]

                            # Keep the maximum overlap value that indicates maximum overlap (aka an inflection point)
                            self.keptOverlapIndices = np.append(self.keptOverlapIndices, maxOverlapPoint - 1)

                            # Clearing buffers
                            self.overlapValBuffer = np.array([])
                            self.overlapIndicesBuffer = np.array([])
            except Exception as e:
                print("-------------------------------------------------------")
                print(e)
                print("Problem using template for inflection point extraction.")



    """
    Description: Base function to be called when utilizing this class.

    param: inputPressDict: 
    param: inputIndDict:
    param: signalIncreaseVal: 
    param: upSampleFact: The length factor that the data needs to be upsampled by. Example: If the data is 
        originally sampled at 66 Hz, and needs to be upsampled to 1980 Hz, then the upsampleFactor is 30.
    """
    def find_template_extract_inds(self, inputPressDict, inputIndDict, upSampleFact, signalIncreaseVal = 20):
        if (inputPressDict.keys() != inputIndDict.keys()):
            print("---------------------------------------------------")
            print("Keys between the two input dictionaries must match.")
            return

        for key in inputPressDict.keys():
            # Upsampling data to 1980 Hz. A window size of 93 has been tested and approved for smoothing
            x, pressData, inflPoints = self.upsample_with_inflections(np.arange(len(inputPressDict[key])), inputPressDict[key], inputIndDict[key], upSampleFact)
            pressData = self.savitzky_golay(pressData, 93, 3)

            self.extract_template(inflPoints, pressData)
            self.find_infl_using_template(pressData, signalIncreaseVal)
            pressDataInflInds = np.array([round(i) for i in self.keptOverlapIndices]) + len(self.template)
            self.inflPointDict[key] = pressDataInflInds + int(0.5*len(self.template))
        
        return self.inflPointDict

