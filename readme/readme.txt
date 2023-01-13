Plugin for CudaText. 

Do transpose operation. This should behave almost like Transpose command in Sublime Text.

* Single caret without selection: Simply swap two characters around the caret (same as Sublime Text or Bash)
* Single caret with text selection: Nothing to transpose
* Multiple carets without selection: Do transpose on each single caret one by one.
* Multiple carets with text selection: Rotate the text selection. (First selection become second, second become third,... , last become first). If some caret don't have the selection, it will be treated differently from Sublime Text: it will be treated as empty selection, while in ST4 this caret will get the forced selection from the word under caret.

Author: ThaiDat

License: MIT