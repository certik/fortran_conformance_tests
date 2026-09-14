subroutine s15524_char4_to_char1()
    implicit none
    character(kind=4, len=1) :: c = 4_"a"
    call s(c)
contains
    subroutine s(x)
        character(kind=1, len=1), intent(in) :: x
    end subroutine
end subroutine
