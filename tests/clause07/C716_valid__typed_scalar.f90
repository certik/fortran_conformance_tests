! rule: C716
! covers: typed-scalar-outside-premise
! evidence: positive-control
program c716_typed_scalar
    implicit none
    integer :: actual = 7
    integer :: seen = -1
    call forward(actual, seen)
    if (seen /= 0) error stop 'typed-scalar-rank'
contains
    subroutine forward(x, observed)
        integer, intent(in) :: x
        integer, intent(out) :: observed
        call sink(x, observed)
    end subroutine
    subroutine sink(x, observed)
        type(*), intent(in) :: x(..)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
