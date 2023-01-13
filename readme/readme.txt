Plugin for CudaText. 
Do transpose operation. This should behave almost like Transpose command in Sublime text.

* Single caret: Simply swap two characters around the caret (same as Sublime Text or Bash)
* Multiple carets: Do transpose on every single caret one by one
* Multiple carets with text selection: Rotate the text selection. (First selection become second, second become third,... , last become first). Notice that caret with single caret will be treated as empty selection.

Author: ThaiDat
License: MIT