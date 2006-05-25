#########################################################################
#
#   BilFile.py - This file is part of the Spectral Python (SPy) package.
#
#   Copyright (C) 2001 Thomas Boggs
#
#   Spectral Python is free software; you can redistribute it and/
#   or modify it under the terms of the GNU General Public License
#   as published by the Free Software Foundation; either version 2
#   of the License, or (at your option) any later version.
#
#   Spectral Python is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#     
#   You should have received a copy of the GNU General Public License
#   along with this software; if not, write to
#
#               Free Software Foundation, Inc.
#               59 Temple Place, Suite 330
#               Boston, MA 02111-1307
#               USA
#
#########################################################################
#
# Send comments to:
# Thomas Boggs, tboggs@users.sourceforge.net
#

'''
Tools for handling files that are band sequential (BSQ).
'''

from SpyFile import SpyFile

class BsqFile(SpyFile):
    '''
    A class to represent image files stored with bands sequential.
    '''

    def __init__(self, params, metadata = None):
        import Spectral
        self.interleave = Spectral.BSQ
        if metadata == None:
            metadata = {}
        SpyFile.__init__(self, params, metadata)        

    def readBand(self, band):
        '''Read a single band from the image.'''

        from array import array
        import Numeric

        vals = array(self.format)
        offset = self.offset + band * self.sampleSize * self.nRows *self.nCols

        f = self.fid
        
        # Pixel format is BSQ, so read the whole band at once.
        f.seek(offset, 0)
        vals.fromfile(f, self.nRows * self.nCols)

        if self.swap:
            vals.byteswap()
        arr = Numeric.array(vals.tolist())
        arr = Numeric.reshape(arr, (self.nRows, self.nCols))

        return arr

    def readBands(self, bands):
        '''Read specified bands from the image.'''

        from array import array
        import Numeric

        f = self.fid

        # Get the type of the Numeric array (must be a better way)
        ta = array(self.format)
        f.seek(self.offset, 0)
        ta.fromfile(f, 1)
        na = Numeric.array(ta.tolist())
        arrType = na.typecode()

        arr = Numeric.zeros((self.nRows, self.nCols, len(bands)), arrType)

        for j in range(len(bands)):
  
            vals = array(self.format)
            offset = self.offset + (bands[j]) * self.sampleSize \
                     * self.nRows * self.nCols

            # Pixel format is BSQ, so read an entire band at time.
            f.seek(offset, 0)
            vals.fromfile(f, self.nRows * self.nCols)

            if self.swap:
                vals.byteswap()
            bandArr = Numeric.array(vals.tolist())
            bandArr = Numeric.reshape(bandArr, (self.nRows, self.nCols))
            arr[:,:,j] = bandArr

        return arr


    def readPixel(self, row, col):
        '''Read the pixel at position (row,col) from the file.'''

        from array import array
        import Numeric

        vals = array(self.format)
        delta = self.sampleSize * (self.nBands - 1)
        offset = self.offset + row * self.nBands * self.nCols \
                 * self.sampleSize + col * self.sampleSize

        f = self.fid
        nPixels = self.nRows * self.nCols

        nCols = self.nCols
        sampleSize = self.sampleSize
        bandSize = sampleSize * nPixels
        rowSize = sampleSize * self.nCols

        for i in range(self.nBands):
            f.seek(self.offset \
                   + i * bandSize\
                   + row * rowSize \
                   + col * sampleSize, 0)
            vals.fromfile(f, 1)

        if self.swap:
            vals.byteswap()
        pixel = Numeric.array(vals.tolist(), self._typecode)

        return pixel

    def readSubRegion(self, rowBounds, colBounds, bands = None):
        '''
        Reads a contiguous rectangular sub-region from the image. First
        arg is a 2-tuple specifying min and max row indices.  Second arg
        specifies column min and max.  If third argument containing list
        of bannd indices is not given, all bands are read.
        '''

        from array import array
        import Numeric

        nSubRows = rowBounds[1] - rowBounds[0] + 1  # Rows in sub-image
        nSubCols = colBounds[1] - colBounds[0] + 1  # Cols in sub-image
        d_row = self.sampleSize * self.nCols * self.nBands
        colStartPos = colBounds[0] * self.sampleSize

        f = self.fid
        f.seek(self.offset, 0)
        
        # Get the type of the Numeric array (must be a better way)
        ta = array(self.format)
        ta.fromfile(f, 1)
        na = Numeric.array(ta.tolist())
        arrType = na.typecode()

        # Increments between bands
        if bands == None:
            # Read all bands.
            bands = range(self.nBands)

        arr = Numeric.zeros((nSubRows, nSubCols, len(bands)), arrType)

        nRows = self.nRows
        nCols = self.nCols
        sampleSize = self.sampleSize
        bandSize = nRows * nCols * sampleSize
        sampleSize = self.sampleSize
        colStartOffset = colBounds[0] * sampleSize
        rowSize = nCols * sampleSize
        rowStartOffset = rowBounds[0] * nCols * sampleSize
        nSubBands = len(bands)

        # Pixel format is BSQ
        for i in bands:
            vals = array(self.format)
            bandOffset = i * bandSize
            for j in range(rowBounds[0], rowBounds[1] + 1):
                f.seek(self.offset \
                       + bandOffset \
                       + rowStartOffset + j * rowSize \
                       + colStartOffset, 0)
                vals.fromfile(f, nSubCols)
            if self.swap:
                vals.byteswap()
            subArray = Numeric.array(vals.tolist())
            subArray = Numeric.reshape(subArray, (nSubRows, nSubCols))
            arr[:,:,i] = Numeric.transpose(subArray)

        return arr
    

    def readSubImage(self, rows, cols, bands = None):
        '''
        Reads a subset of the image. rows and cols are lists
        specifying the row and col indices explicitly (not ranges).
        If third argument containing list of band indices is not given,
        all bands are read.
        '''

        from array import array
        import Numeric

        nSubRows = len(rows)                        # Rows in sub-image
        nSubCols = len(cols)                        # Cols in sub-image
        d_col = self.sampleSize
        d_band = d_col * self.nCols
        d_row = d_band * self.nBands

        f = self.fid
        f.seek(self.offset, 0)
        
        # Get the type of the Numeric array (must be a better way)
        ta = array(self.format)
        ta.fromfile(f, 1)
        na = Numeric.array(ta.tolist())
        arrType = na.typecode()

        # Increments between bands
        if bands == None:
            # Read all bands.
            bands = range(self.nBands)
        nSubBands = len(bands)

        arr = Numeric.zeros((nSubRows, nSubCols, nSubBands), arrType)

        offset = self.offset
        vals = array(self.format)

        nRows = self.nRows
        nCols = self.nCols
        sampleSize = self.sampleSize
        bandSize = nRows * nCols * sampleSize
        sampleSize = self.sampleSize
        rowSize = nCols * sampleSize

        # Pixel format is BSQ
        for i in bands:
            bandOffset = offset + i * bandSize
            for j in rows:
                rowOffset = j * rowSize
                for k in cols:
                    f.seek(bandOffset \
                           + rowOffset \
                           + k * sampleSize, 0)
                    vals.fromfile(f, 1)
        if self.swap:
            vals.byteswap()
        subArray = Numeric.array(vals.tolist())
        subArray = Numeric.reshape(subArray, (nSubRows, nSubCols, nSubBands))

        return subArray

    def readDatum(self, i, j, k):
        '''
        Return the kth band value for pixel (i, j). Using this function
        is not an efficient way to iterate over bands or pixels. For
        such cases, use readBands or readPixel instead.
        '''

        import array

        nRows = self.nRows
        nCols = self.nCols
        sampleSize = self.sampleSize

        self.fid.seek(self.offset \
                      + (k * nRows * nCols \
                         + i * nCols \
                         + j) * sampleSize, 0)
        vals = array.array(self.format)
        vals.fromfile(self.fid, 1)
        return vals.tolist()[0]

        

        

        


        
        
        
        