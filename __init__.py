import cudatext as app
from cudatext import ed


class Command:  
    
    def standardize_pos(self, pos, sel=False):
        '''Ensure x2, y2 hold a bigger position
        pos: tuple (column_from, line_from, column_to, line_to)
        sel: caret is selection. If no, return pos as a empty selection (instead of empty caret pos)
        return standardized pos which (column_to, line_to) > (column_from, line_from)
        '''
        x1, y1, x2, y2 = pos
        if x2 < 0:
            return (x1, y1, x1, y1) if sel else pos 
        elif (y1, x1) > (y2, x2):
            return x2, y2, x1, y1
        return pos

    def get_next_place(self, x, y):
        '''Get the next place 1 step forward from current place (endline counted)
        x, y: Position on editor
        line_len: Length of current line
        line_cnt: Number of lines
        return col, line of the next place 1 step forward
        '''
        if x == len(ed.get_text_line(y)):
            return (0, y + 1) if y < ed.get_line_count() - 1 else (x, y)
        return x + 1, y
            
    def get_prev_place(self, x, y, line_len=None, line_cnt=None):
        '''Get the prev place 1 step forward from current place (endline counted)
        x, y: Position on editor
        return col, line of the prev place 1 step forward
        '''
        if x == 0:
            return (len(ed.get_text_line(y - 1)), y - 1) if y > 0 else (0, 0)
        return x - 1, y        
    
    def do_replace_str(self, s, pos):
        '''Replace text in the given pos
        s: string to put in the pos
        pos: (column_from, line_from, column_to, line_to) tuple. (column_to, line_to) must be bigger than (column_from, line_from) 
        return the caret position after insertion
        ''' 
        x1, y1, x2, y2 = pos
        x_new, y_new = ed.replace(x1, y1, x2, y2, s)
        return x1, y1, x_new, y_new
        
    def do_insert_str(self, s, x, y):
        '''Insert string at given pos
        s: string to put in the pos
        x, y: column, line. Position to insert
        return the caret position after insertion
        '''
        x_new, y_new = ed.insert(x, y, s)
        return x_new, y_new, -1, -1
        
    def do_transpose_single(self, pos):
        '''Apply transpose to the text under caret
        pos: selected area. Value will change the behaviour of this function
            selection: Do nothing
            without selection: transpose or swap 2 nearby characters. (endl count)
        return None
        '''
        x, y, x2, y2 = pos
        # Do nothing if selection
        if x2 < 0:
            # No selection
            _x, _y = self.get_prev_place(x, y)
            x_, y_ = self.get_next_place(x, y)
            # edge case beginning of file. Do nothing, move caret one step forward
            if (_x,_y) == (0,0):
                return x_, y_, -1, -1 
            # edge case end of file. Do nothing
            if (x, y) == (x_,y_):
                return x, y, -1, -1         
            s = ed.get_text_substr(_x, _y, x_, y_)
            #print((_x, _y, x_, y_), s) # Uncomment for debugging
            _, _, x_new, y_new = self.do_replace_str(s[::-1], (_x, _y, x_, y_))
            return x_new, y_new, -1, -1
        else:
            # Selection
            return pos

    def do_transpose_multiple(self, carets):
        '''Apply transpose to multiple carets. 
        If no selection, do transpose single one by one
        If any selection, make all selection. Then transpose among them
        carets: list of positions
        return None
        '''
        sel = any(map(lambda c: c[3] >= 0, carets))
        if sel:
            std_carets = [self.standardize_pos(pos, sel=True) for pos in carets]
            strs = [ed.get_text_substr(*pos) for pos in std_carets]
            # Put the last to top place
            new_carets = [self.do_replace_str(strs[-1], std_carets[0])]
            # Use shift_x, shift_y to adjust the position after replace substr
            shift_y = new_carets[0][3] - std_carets[0][3]
            shift_x = new_carets[0][2] - std_carets[0][2]          

            for i in range(1, len(strs)):
                # reset cumm if needed
                std_x, std_y, std_x2, std_y2 = std_carets[i]
                pre_x, pre_y, pre_x2, pre_y2 = new_carets[i-1]
                shifted_y = std_y + shift_y
                shifted_x = std_x + shift_x if pre_y2 == shifted_y else std_x
                shifted_y2 = std_y2 + shift_y
                shifted_x2 = std_x2 + shift_x if pre_y2 == shifted_y2 else std_x2
                new_pos = self.do_replace_str(strs[i-1], (shifted_x, shifted_y, shifted_x2, shifted_y2))
                new_carets.append(new_pos)
                shift_x = new_pos[2] - std_x2
                shift_y = new_pos[3] - std_y2
            return new_carets            
        else:
            new_carets = [self.do_transpose_single(pos) for pos in carets]
            return new_carets

    def transpose(self):
        '''
        Apply transpose to current edior based on caret place and selection
        '''
        carets = ed.get_carets()
        if len(carets) == 1:
            # single caret
            pos = self.do_transpose_single(carets[0])
            ed.set_caret(*pos)
        else:
            new_carets = iter(self.do_transpose_multiple(carets))
            ed.set_caret(-1, -1, id=app.CARET_DELETE_ALL)
            for pos in new_carets:
                ed.set_caret(*pos, id=app.CARET_ADD)