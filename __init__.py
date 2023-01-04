import cudatext as app
from cudatext import ed


def _standardize_pos(pos):
    '''Ensure x2, y2 hold a bigger position
    pos: tuple (column_from, line_from, column_to, line_to)
    return standardized pos which (column_to, line_to) > (column_from, line_from)
    '''
    x1, y1, x2, y2 = pos
    if x2 < 0:
        return pos
    elif (y1 > y2) or (y1 == y2 and x1 > x2):
        return x2, y2, x1, y1
    else:
        return pos        


class Command:  
    
    def do_replace_str(self, s, pos):
        '''replace text in the given pos
        s: string to put in the pos
        pos: (column_from, line_from, column_to, line_to) tuple.
        return the caret position after insertion
        ''' 
        x1, y1, x2, y2 = _standardize_pos(pos)
        x_new = None; y_new = None
        if x2 < 0: 
            x_new, y_new = ed.insert(x1, y1, s) 
        else:
            x_new, y_new = ed.replace(x1, y1, x2, y2, s)
        return x1, y1, x_new, y_new

    def do_replace_line(self, s, line):
        '''replace line in the given index
        s: string to put in the line
        line: index of line
        return None
        '''
        ed.set_text_line(line, s)
        
    def do_transpose_single(self, pos, direction=1):
        '''Appy transpose to the editor. The behaviour depend on the pos. Caret position unchanged
        pos: selected area. Value will change the behaviour of this function
            selection: Roll the selected text
            single caret somewhere in the middle: Swap (transpose/roll) two nearby characters
            single caret at the beginning/end of line:  Swap (transpose/roll) two nearby lines
        direction: Direction of transpose.
            1: Forward
            -1: Backward
        return None
        '''
        x1, y1, x2, y2 = _standardize_pos(pos)
        if x2 >= 0:
            # Selection
            s = ed.get_text_substr(x1, y1, x2, y2)
            s = s[-1] + s[:-1] if direction > 0 else s[1:] + s[0]
            self.do_replace_str(s, (x1, y1, x2, y2))
        else:
            # Single carret
            curr_line = ed.get_text_line(y1)
            if x1 == 0 and y1 > 0:
                # Beginning of line
                prev_line = ed.get_text_line(y1 - direction)
                self.do_replace_line(curr_line, y1 - direction)
                self.do_replace_line(prev_line, y1)
            elif x1 == len(curr_line) and y1 < ed.get_line_count() - 1:
                # End of line  
                next_line = ed.get_text_line(y1 + direction)
                self.do_replace_line(curr_line, y1 + direction)
                self.do_replace_line(next_line, y1)  
                ed.set_caret(len(next_line), y1)
            elif x1 > 0 and x1 < len(curr_line):
                # Middle of line    
                s = ed.get_text_substr(x1 - 1, y1, x1 + 1, y1)            
                self.do_replace_str(s[::-1], (x1 - 1, y1, x1 + 1, y1))    

    def transpose(self):
        '''
        Apply transpose to current edior based on caret place and selection
        '''
        carets = ed.get_carets()
        if len(carets) == 1:
            self.do_transpose_single(carets[0])
            