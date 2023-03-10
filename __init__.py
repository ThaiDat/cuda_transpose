import cudatext as app
from cudatext import ed
from cudax_lib import get_translation


def is_surrogate(ch):
    '''Check if ch is a char in a surrogate pair
    ch: Single character string
    return True if ch is a valid single char in a surrogate pair (stay in range 0xD800 - 0xDFFF).
    '''
    if len(ch) != 1:
        return False
    ch = ord(ch)
    return 0xD800 <= ch and ch <= 0xDFFF


_ = get_translation(__file__)  # I18N



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

    def get_line_max(self, y):
        '''Get the largest position (column) of current line
        y: line
        return the max columns possible of line y
        '''
        line = ed.get_text_line(y).encode('utf-16')
        if len(line) < 2:
            return len(line)
        if line[0] == 0xff and line[1] == 0xfe:
            return (len(line) - 2) // 2
        else:
            return len(line) // 2

    def get_next_place(self, x, y):
        '''Get the next place 1 step forward from current place (endline counted)
        x, y: Position on editor
        line_len: Length of current line
        line_cnt: Number of lines
        return col, line of the next place 1 step forward
        '''
        if x == self.get_line_max(y):
            return (0, y + 1) if y < ed.get_line_count() - 1 else (x, y)
        return x + 1, y
            
    def get_prev_place(self, x, y, line_len=None, line_cnt=None):
        '''Get the prev place 1 step forward from current place (endline counted)
        x, y: Position on editor
        return col, line of the prev place 1 step forward
        '''
        if x == 0:
            return (self.get_line_max(y - 1), y - 1) if y > 0 else (0, 0)
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
        
    def do_delete_str(self, pos):
        '''Delete string at given pos
        pos: (column_from, line_from, column_to, line_to) tuple. (column_to, line_to) must be bigger than (column_from, line_from) 
        return the caret position after deletion
        '''
        x1, y1, x2, y2 = pos
        ed.delete(x1, y1, x2, y2)
        return x1, y1, -1, -1
    
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
            # Get the next character. Skip 2 char if surrogate pair
            x_, y_ = self.get_next_place(x, y)
            s_ = ed.get_text_substr(x, y, x_, y_)
            if is_surrogate(s_):
                x_, y_ = self.get_next_place(x_, y_)
                s_ = ed.get_text_substr(x, y, x_, y_)
            # edge case beginning of file. Do nothing, move caret one step forward
            if (x,y) == (0,0):
                return x_, y_, -1, -1 
            # edge case end of file. Do nothing
            if (x, y) == (x_,y_):
                app.msg_status(_('Transpose: End of file reached'))
                return x, y, -1, -1         
            # Get previous character, skip 2 chars if surrogate pair
            _x, _y = self.get_prev_place(x, y)
            _s = ed.get_text_substr(_x, _y, x, y)
            if is_surrogate(_s):
                _x, _y = self.get_prev_place(_x, _y)
                _s = ed.get_text_substr(_x, _y, x, y)
            #print((_x, _y, x_, y_), _s, s_) # Uncomment for debugging
            __, __, x_new, y_new = self.do_replace_str(s_ + _s, (_x, _y, x_, y_))
            return x_new, y_new, -1, -1
        else:
            # Selection
            app.msg_status(_('Transpose: Nothing to transpose'))
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


    def caret_valid_for_move(self):
        carets = ed.get_carets()

        # Continue only with one-caret
        if len(carets) != 1:
            return False

        # Continue only with a valid selection
        if carets[0][3] < 0:
            return False

        # Continue only with one-line
        if carets[0][1] != carets[0][3]:
            return False

        return True


    def move_sel_left(self):
        if self.caret_valid_for_move():
            text = ed.get_text_sel()
            caret = ed.get_carets()[0]
            x0, y0, x1, y1 = self.standardize_pos(caret)

            dx = 1
            if (x0>=2) and is_surrogate(ed.get_text_substr(x0-1, y0, x0, y0)):
                dx = 2

            if x0 >= dx:
                ed.delete(x0, y0, x1, y1)
                ed.insert(x0 - dx, y0, text)
                # Preserve selection
                ed.set_caret(x0 - dx, y0, x1 - dx, y1, app.CARET_SET_ONE)
                app.msg_status(_('Transpose: Moved to the left'))
            else:
                app.msg_status(_('Transpose: Start reached'))

        else:
            app.msg_status(_('Transpose: No conditions to move'))

    def move_sel_right(self):
        if self.caret_valid_for_move():
            text = ed.get_text_sel()
            caret = ed.get_carets()[0]
            x0, y0, x1, y1 = self.standardize_pos(caret)
            len_line = self.get_line_max(y0)

            dx = 1 
            if (x1+2<=len_line) and is_surrogate(ed.get_text_substr(x1, y0, x1+1, y0)):
                dx = 2

            if x1 + dx <= len_line:
                ed.delete(x0, y0, x1, y1)
                ed.insert(x0 + dx, y0, text)
                # Preserve selection
                ed.set_caret(x0 + dx, y0, x1 + dx, y1, app.CARET_SET_ONE)
                app.msg_status(_('Transpose: Moved to the right'))
            else:
                app.msg_status(_('Transpose: End reached'))
        else:
            app.msg_status(_('Transpose: No conditions to move'))
