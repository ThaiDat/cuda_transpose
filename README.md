# cuda_transpose
Add-on for CudaText. Do transpose operation

If single caret: Simply swap two character around the caret
If multiple caret without selection: Transpose every single caret one by one
If multiple caret with selections: Rotate selections. Note that caret with no selection will be treated as empty selection.
