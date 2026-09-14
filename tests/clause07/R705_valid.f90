! rule: R705
! covers: without-selector with-selector
! evidence: positive-control
program p
    implicit none
    integer :: a = 17
    integer(kind=kind(0)) :: b = -23
    call check(a, 17)
    call check(b, -23)
contains
    subroutine check(value, expected)
        integer, intent(in) :: value, expected
        if (value /= expected) error stop 1
    end subroutine
end program
