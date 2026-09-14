! rule: C715
! covers: assumed-type-forwarding
! evidence: positive-control
program c715_forwarding
    implicit none
    integer :: actual(3) = [2, 3, 5]
    integer :: seen = -1
    call forward(actual, seen)
    if (seen /= 3) error stop 'forwarded-size'
contains
    subroutine forward(x, observed)
        type(*), intent(in) :: x(:)
        integer, intent(out) :: observed
        call sink(x, observed)
    end subroutine
    subroutine sink(x, observed)
        type(*), intent(in) :: x(:)
        integer, intent(out) :: observed
        observed = size(x)
    end subroutine
end program
