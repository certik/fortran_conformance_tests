! rule: C716
! covers: assumed-shape-forwarding
! evidence: positive-control
program c716_assumed_shape
    implicit none
    integer :: actual(2, 3) = 7
    integer :: seen = -1
    call forward(actual, seen)
    if (seen /= 2) error stop 'forwarded-rank'
contains
    subroutine forward(x, observed)
        type(*), intent(in) :: x(:, :)
        integer, intent(out) :: observed
        call sink(x, observed)
    end subroutine
    subroutine sink(x, observed)
        type(*), intent(in) :: x(..)
        integer, intent(out) :: observed
        observed = rank(x)
    end subroutine
end program
