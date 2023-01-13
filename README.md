Plugin for CudaText. 

Do transpose operation. This should behave almost like Transpose command in Sublime Text.

* Single caret without selection: Simply swap two characters around the caret (same as Sublime Text or Bash)
* Single caret with text selection: Nothing happen
* Multiple carets without selection: For each caret, swap two chars around caret.
* Multiple carets with text selection: Rotate the text selection. (First selection become second, second become third,... , last become first). Notice that caret with no selection will be treated as empty selection (different from Sublime Text)

Author: ThaiDat

License: MIT