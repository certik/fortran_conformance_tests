function character_external(expected) result(text)
    implicit none
    integer, intent(in) :: expected
    character(*) :: text
    if (len(text) /= expected) error stop 1
    text = 'ABCDE'
end function
