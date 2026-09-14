subroutine s15524_logical1_to_logical4()
    implicit none
    logical(1) :: l = .true._1
    call s(l)
contains
    subroutine s(x)
        logical(1), intent(in) :: x
    end subroutine
end subroutine
