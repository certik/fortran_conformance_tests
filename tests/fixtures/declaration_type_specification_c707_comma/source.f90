program c707_comma
    implicit none
    type(character*3,) word
    word = 'abc'
    if (len(word) /= 3) error stop 'length'
    if (word /= 'abc') error stop 'value'
end program
